/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { renderToString } from "@web/core/utils/render";
import { SignablePDFIframe } from "@sign/components/sign_request/signable_PDF_iframe";
import { EditablePDFIframeMixin } from "@sign/backend_components/editable_pdf_iframe_mixin";
import { patch } from "@web/core/utils/patch";


patch(SignablePDFIframe.prototype, {
 enableCustom(signItem) {
        super.enableCustom(signItem);
         if (this.readonly || signItem.data.responsible !== this.currentRole) {
            return;
        }
        const signItemElement = signItem.el;
        const signItemData = signItem.data;
        const signItemType = this.signItemTypesById[signItemData.type_id];
        const { name, item_type: type, auto_value: autoValue } = signItemType;
        if (name === _t("Date")) {
            signItemElement.addEventListener("focus", (e) => {
                this.fillTextSignItem(e.currentTarget, this.signInfo.get('todayFormattedDate'));
            });
        } else if (type === "signature" || type === "initial") {
            signItemElement.addEventListener("click", (e) => {
                this.handleSignatureDialogClick(e.currentTarget, signItemType);
            });
        } else if (type === "radio") {
            signItemElement.addEventListener("click", (e) => {
                this.handleRadioItemSelected(signItem);
            })
        }

         if (autoValue && ["text", "textarea"].includes(type)) {
              signItemElement.value = autoValue;
        }

        if (type === "selection") {
            if (signItemElement.value) {
                this.handleInput();
            }
            const optionDiv = signItemElement.querySelector(".o_sign_select_options_display");
            optionDiv.addEventListener("click", (e) => {
                if (e.target.classList.contains("o_sign_item_option")) {
                    const option = e.target;
                    const selectedValue = option.dataset.id;
                    signItemElement.value = selectedValue;
                    option.classList.add("o_sign_selected_option");
                    option.classList.remove("o_sign_not_selected_option");
                    const notSelected = optionDiv.querySelectorAll(
                        `.o_sign_item_option:not([data-id='${selectedValue}'])`
                    );
                    [...notSelected].forEach((el) => {
                        el.classList.remove("o_sign_selected_option");
                        el.classList.add("o_sign_not_selected_option");
                    });
                    this.handleInput();
                }
            });
        }

        signItemElement.addEventListener("input", this.handleInput.bind(this));

 }
});