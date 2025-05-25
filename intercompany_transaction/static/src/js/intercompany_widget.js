/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

class IntercompanyWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            hasIntercompany: false,
            intercompanyName: "",
            intercompanyId: false,
        });

        onWillStart(async () => {
            await this.fetchIntercompanyData();
        });
    }

    async fetchIntercompanyData() {
        const model = this.props.record.resModel;
        const recordId = this.props.record.resId;
        
        if (!recordId) return;
        
        if (model === 'purchase.order') {
            const result = await this.orm.read('purchase.order', [recordId], ['intercompany_sale_order_id']);
            if (result && result.length > 0 && result[0].intercompany_sale_order_id) {
                this.state.hasIntercompany = true;
                this.state.intercompanyId = result[0].intercompany_sale_order_id[0];
                this.state.intercompanyName = result[0].intercompany_sale_order_id[1];
            }
        } else if (model === 'sale.order') {
            const result = await this.orm.read('sale.order', [recordId], ['auto_purchase_order_id']);
            if (result && result.length > 0 && result[0].auto_purchase_order_id) {
                this.state.hasIntercompany = true;
                this.state.intercompanyId = result[0].auto_purchase_order_id[0];
                this.state.intercompanyName = result[0].auto_purchase_order_id[1];
            }
        }
    }

    async openIntercompanyRecord() {
        const model = this.props.record.resModel === 'purchase.order' ? 'sale.order' : 'purchase.order';
        
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: model,
            res_id: this.state.intercompanyId,
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

IntercompanyWidget.template = 'intercompany_transaction.IntercompanyWidget';
IntercompanyWidget.supportedTypes = ['char'];

registry.category('fields').add('intercompany_widget', IntercompanyWidget);
