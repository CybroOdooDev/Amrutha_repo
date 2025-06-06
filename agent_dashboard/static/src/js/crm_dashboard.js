/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, useState } from "@odoo/owl";
import { user } from "@web/core/user";
import { PieChart } from "./PieChart"; // Import the PieChart component
import { GoalVsActualChart } from "./GoalVsActualChart";

export class CRMDashboard extends Component {
    static components = { PieChart, GoalVsActualChart }; // Register the PieChart component
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
            totalAskingPrice: 0, //
            totalProperties: 0, //
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
            stageLabels: [], // Dynamic labels for the pie chart
            totalActivities: 0,
            plannedActivities: 0,
            overdueActivities: 0,
            todayActivities: 0,
            activityList: [], // To store the list of activities
            isLoadingActivities: true,
            errorActivities: null,
            avgDaysToClose: 0,
            avgClosePrice: '0',
            salesVolume: '0',
            closedTransactions: 0,
            leadToClientCount: 0,
            priceChangePercentage: 0,

        });
        // Bind `this` to the method
        this.removeTask = this.removeTask.bind(this);
        this.toggleTaskCompletion = this.toggleTaskCompletion.bind(this);

        // Fetch data when the component is about to start
        onWillStart(async () => {
            await this.fetchDashboardData();
            await this.fetchWeeklyTasks();
            await this.fetchStageData(); // Fetch stage labels
            await this.fetchGoalVsActualData(); // Fetch data for Goal vs Actual chart
            await this.fetchActivityData(); // Fetch activity data
        });
    }

    /**
 * Fetch activity data from the crm.lead model.
 */
async fetchActivityData() {
    try {
        const activities = await this.orm.searchRead(
            'crm.lead', // Model name
            [], // Domain (empty to fetch all records)
            ['activity_ids'], // Fields to fetch
        );

        // Flatten the list of activities
        const allActivities = activities.flatMap(lead => lead.activity_ids);

        // Fetch detailed activity data
        const activityDetails = await this.orm.searchRead(
            'mail.activity', // Model name
            [['id', 'in', allActivities]], // Domain to fetch only relevant activities
            ['summary', 'date_deadline', 'state'], // Fields to fetch
        );

        // Calculate counts
        const today = new Date().toISOString().split('T')[0];
        this.state.totalActivities = activityDetails.length;
        this.state.plannedActivities = activityDetails.filter(activity => activity.state === 'planned').length;
        this.state.overdueActivities = activityDetails.filter(activity => activity.state === 'overdue').length;
        this.state.todayActivities = activityDetails.filter(activity => activity.date_deadline === today).length;

        // Update the activity list
        this.state.activityList = activityDetails;

        this.state.isLoadingActivities = false;
    } catch (error) {
        console.error("Error fetching activity data:", error);
        this.state.errorActivities = _t("Failed to load activity data. Please try again later.");
        this.state.isLoadingActivities = false;
    }
}
    /**
     * Fetch data for the Goal vs Actual chart, grouped by months and filtered for the current year.
     */
    async fetchGoalVsActualData() {
        try {
            // Get the current year
            const currentYear = new Date().getFullYear();

            // Fetch leads created in the current year
            const leads = await this.orm.searchRead(
                'crm.lead', // Model name
                [
                    ['create_date', '>=', `${currentYear}-01-01`], // Filter for the current year
                    ['create_date', '<=', `${currentYear}-12-31`],
                ],
                [
                    'total_commission',
                    'commission_to_be_paid',
                    'total_commercial_commission',
                    'total_commercial_commission_earned',
                    'company_id',
                    'create_date', // Include create_date to group by month
                ],
            );

            // Extract unique company IDs from the leads
            const companyIds = [...new Set(leads.map(lead => lead.company_id[0]))];

            // Fetch company details for the unique company IDs
            const companies = await this.orm.searchRead(
                'res.company', // Model name
                [['id', 'in', companyIds]], // Domain to fetch only relevant companies
                ['id', 'is_calculate_commission', 'is_calculate_commercial_commission'], // Fields to fetch
            );

            // Create a map of company ID to company details for quick lookup
            const companyMap = {};
            companies.forEach(company => {
                companyMap[company.id] = company;
            });

            // Initialize arrays to store monthly data
            const monthlyGoalData = new Array(12).fill(0); // 12 months, initialized to 0
            const monthlyActualData = new Array(12).fill(0); // 12 months, initialized to 0

            // Iterate through leads and aggregate data by month
            leads.forEach(lead => {
                const createDate = new Date(lead.create_date); // Convert create_date to a Date object
                const month = createDate.getMonth(); // Get the month (0 = January, 11 = December)

                const companyId = lead.company_id[0]; // Get the company ID
                const company = companyMap[companyId]; // Get the company details

                if (company && company.is_calculate_commission) {
                    // Use total_commission and commission_to_be_paid fields
                    monthlyGoalData[month] += lead.total_commission || 0;
                    monthlyActualData[month] += lead.commission_to_be_paid || 0;
                } else if (company && company.is_calculate_commercial_commission) {
                    // Use total_commercial_commission and total_commercial_commission_earned fields
                    monthlyGoalData[month] += lead.total_commercial_commission || 0;
                    monthlyActualData[month] += lead.total_commercial_commission_earned || 0;
                }
            });

            // Update the state with the fetched data
            this.state.goalData = monthlyGoalData;
            this.state.actualData = monthlyActualData;
            console.log(this.state.goalData,"this.state.goalData")
            console.log(this.state.actualData,"this.state.actualData")
            this.state.isLoadingGoalVsActual = false; // Data has been loaded
        } catch (error) {
            console.error("Error fetching Goal vs Actual data:", error);
            this.state.errorGoalVsActual = _t("Failed to load Goal vs Actual data. Please try again later.");
            this.state.isLoadingGoalVsActual = false; // Stop loading
        }
    }
    /**
     * Fetch stage labels and data from the crm.lead model.
     */
    async fetchStageData() {
        try {
            const leads = await this.orm.searchRead(
                'crm.lead', // Model name
                [['x_studio_opportunity_stage', '!=', false]], // Domain to filter leads with a stage
                ['x_studio_opportunity_stage'], // Fields to fetch
            );

            console.log("Fetched leads:", leads); // Debugging log

            // Group leads by stage and count them
            const stageCounts = {};
            leads.forEach(lead => {
                const stage = lead.x_studio_opportunity_stage; // Corrected field name
                if (stage && stage[1]) { // Check if stage exists and has a display name
                    const stageName = stage[1]; // Get the stage name
                    if (stageCounts[stageName]) {
                        stageCounts[stageName]++;
                    } else {
                        stageCounts[stageName] = 1;
                    }
                } else {
                    console.log("Lead with undefined or invalid stage:", lead); // Debugging log
                }
            });

            console.log("Stage counts:", stageCounts); // Debugging log

            // Extract labels and data
            this.state.stageLabels = Object.keys(stageCounts);
            this.state.stageData = Object.values(stageCounts);

            console.log("Stage labels:", this.state.stageLabels); // Debugging log
            console.log("Stage data:", this.state.stageData); // Debugging log
        } catch (error) {
            console.error("Error fetching stage data:", error);
            this.state.error = _t("Failed to load stage data. Please try again later.");
        }
    }
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(value);
    }
    /**
     * Open the Payout Summary list view
     */
    async openPayoutSummary() {
        try {
            // Search for the commission product
            const product = await this.orm.searchRead(
                'product.product',
                [
                    ['name', '=', 'Commission'],
                    ['default_code', '=', 'COMMISSION']
                ],
                ['id'],
                { limit: 1 }
            );

            if (product.length > 0) {
                const productId = product[0].id;

                // Open the list view of account.move filtered by:
                // - Current user's moves
                // - With the commission product
                this.env.services['action'].doAction({
                    type: 'ir.actions.act_window',
                    name: _t('Payout Summary'),
                    res_model: 'account.move',
                    views: [[false, 'list'], [false, 'form']],
                    domain: [
//                        ['invoice_user_id', '=', this.user.userId],
//                        ['invoice_line_ids.product_id', '=', productId],
                        ['move_type', 'in', ['in_invoice']]
                    ],
                    context: {
                        search_default_filter_posted: 1,
                        create: false
                    }
                });
            } else {
                this.state.error = _t("Commission product not found.");
            }
        } catch (error) {
            console.error("Error opening payout summary:", error);
            this.state.error = _t("Failed to open payout summary. Please try again later.");
        }
    }
    /**
     * Fetch dashboard data from the backend.
     */
    async fetchDashboardData() {
        try {
            // Fetch dashboard summary data
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
            this.state.totalAskingPrice = data.totalAskingPrice;
            this.state.totalProperties = data.totalProperties;
            this.state.avgDaysToClose = data.avgDaysToClose;
            this.state.avgClosePrice = this.formatCurrency(data.avgClosePrice);
            this.state.salesVolume = this.formatCurrency(data.salesVolume);
            this.state.closedTransactions = data.closedTransactions;
            this.state.leadToClientCount = data.leadToClientCount;
            console.log(data ,"data")
            console.log(data.totalAskingPrice ,"totalAskingPrice")
            console.log(this.state.totalProperties,"totalProperties")
            // Fetch property details from crm.lead
            const leads = await this.orm.searchRead(
                'crm.lead', // Model name
                [], // Domain (empty to fetch all records)
                [
                    'partner_id', // Client Name
                    'x_studio_property_address', // Property
                    'total_sales_price', // Total Sales Price (primary price field)
                    'total_list_price', // List Price (fallback price field)
                    'minimum_commission_due', // Minimum Commission Due
                    'date_deadline', // Estimated Closing Date
                    'company_id', // Company ID to check the condition
                ],
            );

            // Fetch company details for all unique company IDs
            const companyIds = [...new Set(leads.map(lead => lead.company_id[0]))];
            const companies = await this.orm.searchRead(
                'res.company', // Model name
                [['id', 'in', companyIds]], // Domain to fetch only relevant companies
                ['id', 'is_calculate_commercial_commission'], // Fields to fetch
            );

            // Create a map of company ID to company details for quick lookup
            const companyMap = {};
            companies.forEach(company => {
                companyMap[company.id] = company;
            });

            // Map the fetched leads to the required format
            this.state.propertyDetails = leads.map(lead => {
                // Determine price - use total_sales_price if available, otherwise use list_price
                const price = lead.total_sales_price || lead.total_list_price || 0;
                // Use minimum_commission_due for estimated commission
                const estimatedCommission = lead.minimum_commission_due || 0;

                return {
                    clientName: lead.partner_id ? lead.partner_id[1] : 'N/A',
                    property: lead.x_studio_property_address || 'N/A',
                    city: lead.partner_id && lead.partner_id[2] ? lead.partner_id[2] : 'N/A',
                    price: this.formatCurrency(price),
                    estimatedCommission: this.formatCurrency(estimatedCommission),
                    estimatedClosingDate: lead.date_deadline || 'N/A',
                };
            });


            this.state.isLoading = false; // Data has been loaded
        } catch (error) {
            this.state.error = _t("Failed to load dashboard data. Please try again later.");
            this.state.isLoading = false; // Stop loading
            console.error("Error fetching dashboard data:", error);
        }
    }
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    /**
     * Fetch weekly tasks from the backend.
     */
    async fetchWeeklyTasks() {
        try {
            const tasks = await this.orm.searchRead(
                'crm.weekly.task',
                [['user_id', '=', this.user.userId]],
                ['name', 'day', 'completed'] // Make sure 'completed' is included
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

            // Force reactivity
            this.state.tasks = { ...this.state.tasks };
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
                const [taskId] = await this.orm.create('crm.weekly.task', [{
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
                    active: true,
                });

                // Clear the input field
                this.state.newTask = "";

                // Trigger reactivity
                this.state.tasks = { ...this.state.tasks };

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
            // Find which day the task belongs to
            const day = Object.keys(this.state.tasks).find(day =>
                this.state.tasks[day].some(task => task.id === taskId)
            );

            if (day) {
                const taskIndex = this.state.tasks[day].findIndex(task => task.id === taskId);
                if (taskIndex !== -1) {
                    const task = this.state.tasks[day][taskIndex];
                    const newCompletedStatus = !task.completed;

                    // Update the task in the backend first
                    await this.orm.write('crm.weekly.task', [taskId], {
                        completed: newCompletedStatus,
                    });

                    // Then update the frontend state
                    this.state.tasks[day][taskIndex].completed = newCompletedStatus;

                    // Force a re-render by creating a new tasks object
                    this.state.tasks = { ...this.state.tasks };
                    }
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