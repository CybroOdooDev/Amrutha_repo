/** @odoo-module **/
import { Component, onWillStart, onMounted, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class PieChart extends Component {
    static props = {
        labels: { type: Array, optional: true }, // Dynamic labels passed as a prop
    };

    setup() {
        super.setup();
        this.canvasEl = useRef("canvas"); // Use the useRef hook to reference the canvas element

        onWillStart(async () => {
            // Lazy load Chart.js
            await loadJS("/web/static/lib/Chart/Chart.js");
        });

        onMounted(() => {
            // Render the pie chart after the component is mounted
            this.renderChart();
        });
    }

    /**
     * Render the pie chart.
     */
    renderChart() {
        const ctx = this.canvasEl.el.getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: this.props.labels || [' '], // Use dynamic labels
                datasets: [{
                    data: this.props.data, // Example data (you can make this dynamic too)
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: false, // Disable responsive behavior
                maintainAspectRatio: false, // Allow the chart to stretch
            }
        });
    }
}

PieChart.template = "PieChart"; // Link the component to the template