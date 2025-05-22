/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BusinessSummaryDashboard extends Component {
    static template = "agent_dashboard.BusinessSummaryDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.leadChartRef = useRef("leadChart");
        this.commissionChartRef = useRef("commissionChart");

        this.leadChartInstance = null;
        this.commissionChartInstance = null;

        this.state = useState({
            isLoading: true,
            error: null,
            years: [2023, 2024, 2025],
            leadData: {},
            salespersonData: [],
            commissionData: {
                commissions: {},
                transactions: {}
            },
            months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            chartColors: [
                'rgba(255, 99, 132, 0.7)',
                'rgba(54, 162, 235, 0.7)',
                'rgba(255, 206, 86, 0.7)',
                'rgba(75, 192, 192, 0.7)',
                'rgba(153, 102, 255, 0.7)'
            ]
        });

        onWillStart(async () => {
            await this.fetchAllData();
        });

        onMounted(() => {
            this.initializeCharts();
        });
    }

    async fetchAllData() {
        try {
            this.state.isLoading = true;
            const data = await this.orm.call(
                "crm.lead",
                "get_dashboard_year_data",
                [this.state.years]
            );

            // Initialize with proper structure
            this.state.leadData = data.lead_data?.monthly_counts || {};
            this.state.salespersonData = data.lead_data?.salespersons || [];

            // Ensure commission data has arrays for all years
            this.state.commissionData = {
                commissions: this.normalizeCommissionData(data.commission_data?.commissions),
                transactions: this.normalizeCommissionData(data.commission_data?.transactions)
            };

        } catch (error) {
            this.state.error = "Failed to load dashboard data";
            console.error("Dashboard data error:", error);
        } finally {
            this.state.isLoading = false;
            this.initializeCharts();
        }
    }

    normalizeCommissionData(data = {}) {
        const normalized = {};
        this.state.years.forEach(year => {
            normalized[year] = Array.isArray(data[year]) && data[year].length === 12
                ? data[year]
                : Array(12).fill(0);
        });
        return normalized;
    }

    initializeCharts() {
        if (this.state.isLoading) return;

        try {
            this.initializeLeadChart();
            this.initializeCommissionChart();
        } catch (error) {
            console.error("Chart initialization error:", error);
        }
    }

    initializeLeadChart() {
        this.destroyChart(this.leadChartInstance);

        if (!this.leadChartRef.el) return;

        try {
            this.leadChartInstance = this.createLeadChart();
        } catch (error) {
            console.error("Lead chart creation error:", error);
        }
    }

    createLeadChart() {
        const ctx = this.leadChartRef.el.getContext('2d');
        const datasets = this.state.years.map((year, index) => ({
            label: year.toString(),
            data: this.getMonthlyData(year, this.state.leadData),
            backgroundColor: this.state.chartColors[index],
            borderColor: this.state.chartColors[index].replace('0.7', '1'),
            borderWidth: 1
        }));

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: this.state.months,
                datasets: datasets.filter(d => d.data.some(v => v !== 0))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Leads by Month'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Leads'
                        },
                        ticks: {
                            precision: 0 // This ensures no decimal places
                        }
                    },
                    x: {
                        ticks: {
                            precision: 0 // This ensures no decimal places for x-axis (months)
                        }
                    }
                }
            }
        });
    }

    initializeCommissionChart() {
        this.destroyChart(this.commissionChartInstance);

        if (!this.commissionChartRef.el) {
            console.warn("Commission chart element not found");
            return;
        }

        try {
            const ctx = this.commissionChartRef.el.getContext('2d');
            if (!ctx) {
                console.warn("Could not get 2D context for commission chart");
                return;
            }

            const { commissions, transactions } = this.state.commissionData;

            // Filter years that have at least some data
            const validYears = this.state.years.filter(year =>
                commissions[year].some(v => v !== 0) ||
                transactions[year].some(v => v !== 0)
            );

            if (validYears.length === 0) {
                console.warn("No valid commission data available");
                return;
            }

            this.commissionChartInstance = this.createCommissionChart(ctx, validYears);
        } catch (error) {
            console.error("Commission chart initialization error:", error);
        }
    }

    createCommissionChart(ctx, validYears) {
        const { commissions, transactions } = this.state.commissionData;

        const datasets = [];

        // Add commission bars
        validYears.forEach((year, index) => {
            datasets.push({
                label: `Commission ${year}`,
                data: commissions[year],
                backgroundColor: this.state.chartColors[index],
                borderColor: this.state.chartColors[index].replace('0.7', '1'),
                borderWidth: 1,
                type: 'bar',
                yAxisID: 'y'
            });
        });

        // Add transaction lines
        validYears.forEach((year, index) => {
            datasets.push({
                label: `Transactions ${year}`,
                data: transactions[year],
                borderColor: this.state.chartColors[index].replace('0.7', '1'),
                backgroundColor: 'transparent',
                borderWidth: 2,
                type: 'line',
                pointRadius: 4,
                yAxisID: 'y1'
            });
        });

        return new Chart(ctx, {
            type: 'bar', // Base chart type
            data: {
                labels: this.state.months,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Commissions & Transactions'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Commission ($)'
                        },
                        beginAtZero: true,
                        ticks: {
                            precision: 0 // No decimals for commission values
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Transactions'
                        },
                        grid: {
                            drawOnChartArea: false
                        },
                        beginAtZero: true,
                        ticks: {
                            precision: 0 // No decimals for transaction counts
                        }
                    },
                    x: {
                        ticks: {
                            precision: 0 // No decimals for month labels
                        }
                    }
                }
            }
        });
    }

    getMonthlyData(year, data) {
        return this.state.months.map((_, month) => {
            const monthStr = (month + 1).toString().padStart(2, '0');
            const key = `${year}-${monthStr}`;
            return data[key] || 0;
        });
    }

    destroyChart(chartInstance) {
        try {
            if (chartInstance && typeof chartInstance.destroy === 'function') {
                chartInstance.destroy();
            }
        } catch (error) {
            console.error("Chart destruction error:", error);
        }
    }

    willUnmount() {
        this.destroyChart(this.leadChartInstance);
        this.destroyChart(this.commissionChartInstance);
    }
}

registry.category("actions").add("business_summary_dashboard", BusinessSummaryDashboard);