/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
const { onWillStart } = owl
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";

// the controller usually contains the Layout and the renderer.
class CustomTreeController extends ListController {
	setup() {
		super.setup();
		this.orm = useService("orm");
	}
	/** function validate button **/
	async OnclickValidate() {
		this.actionService.doAction("soft_reload")
		var action = {
			'type': 'ir.actions.report',
			'data': {
				'model': 'product.return.dates',
				'output_format': 'xlsx',
				'report_name': 'Dispatch Schedule Report',
			},
			'report_type': 'xlsx',
		}
		if (action.report_type === 'xlsx') {

			BlockUI;
			await download({
				url: '/xlsx_reports',
				data: action.data,
				complete: () => unblockUI,
				error: (error) => self.call('crash_manager', 'rpc_error', error),
			});

		}
	}

}

CustomTreeController.template = "dispatch_schedule_report.dispatch_schedule";
export const customTreeView = {
	...listView, // contains the default Renderer/Controller/Model
	Controller: CustomTreeController,
};

// Register it to the views registry
registry.category("views").add("dispatch_schedule", customTreeView);