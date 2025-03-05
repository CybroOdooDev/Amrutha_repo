/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

export class CRMDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService('orm'); // ORM service to interact with the backend
        this.user = user; // Current logged-in user
        this.state = useState({
            agentName: this.user.name, // Set the agent name to the logged-in user's name
            currentPayout: null, // Will be fetched from the backend
            ltmCommissions: null, // Last Twelve Months Commissions
            closingThisWeek: null, // Number of deals closing this week
            expiringThisMonth: null, // Amount expiring this month
            closingThisMonth: null, // Number of deals closing this month
            isLoading: true, // Loading state
            error: null, // Error state
            tasks: { // Tasks organized by day
                monday: [],
                tuesday: [],
                wednesday: [],
                thursday: [],
                friday: [],
                saturday: [],
                sunday: [],
            },
            newTask: "", // Input field for adding a new task
            selectedDay: "monday", // Default selected day for adding tasks
            weekStartDate: this.getWeekStartDate(), // Add weekStartDate to state

        });
        // Bind `this` to the method
        this.removeTask = this.removeTask.bind(this);

        // Fetch data when the component is about to start
        onWillStart(async () => {
            await this.fetchDashboardData();
            await this.fetchWeeklyTasks();
        });
    }

    /**
     * Fetch dashboard data from the backend.
     */
    async fetchDashboardData() {
        try {
            const data = await this.orm.call(
                'crm.lead', // Model name
                'get_dashboard_data', // Method name
                [ ,], // Arguments
                { context: session.user_context } // Context
            );

            // Update the state with fetched data
            this.state.currentPayout = data.currentPayout;
            this.state.ltmCommissions = data.ltmCommissions;
            this.state.closingThisWeek = data.closingThisWeek;
            this.state.expiringThisMonth = data.expiringThisMonth;
            this.state.closingThisMonth = data.closingThisMonth;
            this.state.isLoading = false; // Data has been loaded
        } catch (error) {
            this.state.error = _t("Failed to load dashboard data. Please try again later.");
            this.state.isLoading = false; // Stop loading
            console.error("Error fetching dashboard data:", error);
        }
    }

    /**
     * Fetch weekly tasks from the backend.
     */
    async fetchWeeklyTasks() {
        try {
            const tasks = await this.orm.searchRead(
                'crm.weekly.task', // Model name
                [['user_id', '=', this.user.userId]], // Domain to filter tasks for the current user
                ['name', 'day', 'completed'] // Fields to fetch
            );

            // Organize tasks by day
            this.state.tasks = {
                monday: tasks.filter(task => task.day === 'monday'),
                tuesday: tasks.filter(task => task.day === 'tuesday'),
                wednesday: tasks.filter(task => task.day === 'wednesday'),
                thursday: tasks.filter(task => task.day === 'thursday'),
                friday: tasks.filter(task => task.day === 'friday'),
                saturday: tasks.filter(task => task.day === 'saturday'),
                sunday: tasks.filter(task => task.day === 'sunday'),
            };
        } catch (error) {
            console.error("Error fetching weekly tasks:", error);
            this.state.error = _t("Failed to load weekly tasks. Please try again later.");
        }
    }

    /**
     * Add a new task to the selected day.
     */
    async addTask() {
        if (this.state.newTask.trim() !== "") {
            try {
                // Create the task in the backend
                const taskId = await this.orm.create('crm.weekly.task', [{
                    name: this.state.newTask.trim(),
                    day: this.state.selectedDay,
                    user_id: this.user.userId,
                    completed: false,
                }]);

                // Add the task to the frontend state
                this.state.tasks[this.state.selectedDay].push({
                    id: taskId,
                    name: this.state.newTask.trim(),
                    day: this.state.selectedDay,
                    completed: false,
                });

                // Clear the input field
                this.state.newTask = "";

                // Force a re-render by updating the state
                this.state.tasks = { ...this.state.tasks }; // Create a new object to trigger reactivity
            } catch (error) {
                console.error("Error adding task:", error);
                this.state.error = _t("Failed to add task. Please try again later.");
            }
        }
    }

    /**
     * Toggle the completion status of a task.
     * @param {number} taskId - The ID of the task to toggle.
     */
    async toggleTaskCompletion(taskId) {
        try {
            const task = this.state.tasks[this.state.selectedDay].find(task => task.id === taskId);
            if (task) {
                // Update the task in the backend
                await this.orm.write('crm.weekly.task', [taskId], {
                    completed: !task.completed,
                });

                // Update the task in the frontend state
                task.completed = !task.completed;

                // Force a re-render by updating the state
                this.state.tasks = { ...this.state.tasks }; // Create a new object to trigger reactivity
            }
        } catch (error) {
            console.error("Error toggling task completion:", error);
            this.state.error = _t("Failed to toggle task completion. Please try again later.");
        }
    }

    /**
     * Remove a task from the specified day.
     * @param {number} taskId - The ID of the task to remove.
     * @param {string} day - The day from which to remove the task.
     */
    async removeTask(taskId, day) {
        console.log(taskId, "taskId");
        console.log(this, "this");
        const id = taskId
        try {
            if (!taskId || typeof taskId !== 'number') {
                // Extract the value from the Proxy-wrapped array
                const id = taskId[0]; // Access the first element of the array
                console.log(id, "id"); // 27

            }
            console.log(this, "this");
            console.log(this.orm, "this.orm");

            // Delete the task from the backend
            await this.orm.unlink('crm.weekly.task', [parseInt(id)]);
//            this.model.load();

            // Update the frontend state by removing the task
            this.state.tasks[day] = this.state.tasks[day].filter(task => task.id !== taskId);

            // Force a re-render by updating the state
            this.state.tasks = { ...this.state.tasks }; // Create a new object to trigger reactivity
        } catch (error) {
            console.error("Error removing task:", error);
            this.state.error = _t("Failed to remove task. Please try again later.");
        }
    }
    /**
     * Get the start date of the current week (Monday).
     */
    getWeekStartDate() {
        const today = new Date();
        const dayOfWeek = today.getDay(); // 0 (Sunday) to 6 (Saturday)
        const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Adjust to Monday
        const monday = new Date(today.setDate(diff));
        return monday.toISOString().split('T')[0]; // Format as YYYY-MM-DD
    }
}
// Template for the CRM Dashboard
CRMDashboard.template = 'agent_dashboard.CRMDashboard';

// Register the client action
registry.category("actions").add("crm_dashboard", CRMDashboard);