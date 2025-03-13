/** @odoo-module **/
import { Component, onWillStart, onMounted, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class GoalVsActualChart extends Component {
    static props = {
        goalData: { type: Array, optional: true }, // Goal data passed as a prop
        actualData: { type: Array, optional: true }, // Actual data passed as a prop
    };

    setup() {
        super.setup();
        this.canvasEl = useRef("canvas"); // Use the useRef hook to reference the canvas element

        onWillStart(async () => {
            // Lazy load Chart.js
            await loadJS("/web/static/lib/Chart/Chart.js");
        });

        onMounted(() => {
            // Render the line chart after the component is mounted
            this.renderChart();
        });
    }

    renderChart() {
        // Convert Proxy objects to plain arrays and normalize data
        const goalData = [...this.props.goalData].map(value => value / 1000000); // Convert to millions
        const actualData = [...this.props.actualData].map(value => value / 1000000); // Convert to millions

        console.log("Goal Data (normalized):", goalData);
        console.log("Actual Data (normalized):", actualData);

        const ctx = this.canvasEl.el.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['January', 'February', 'March', 'April', 'May',
                'June', 'July','August','September','October','November',
                'December'],
                datasets: [
                    {
                        label: 'Actual',
                        data: actualData || [' '],
                        backgroundColor: '#0000ff',
                        borderColor: '#0000ff',
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'line',
                        fill: false
                    },
                    {
                        label: 'Goal',
                        data: goalData || [' '],
                        backgroundColor: '#71d927',
                        borderColor: '#71d927',
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'line',
                        fill: false
                    }
                ]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    },
                },
                responsive: false,
                maintainAspectRatio: false,
            }
        });
    }
}

GoalVsActualChart.template = "GoalVsActualChart"; // Link the component to the template