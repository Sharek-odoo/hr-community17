/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { getDefaultConfig } from "@web/views/view";
import { ChartRenderer } from "../chart_renderer/chart_renderer";
import { PieChart } from "../chart_renderer/pie_chart";
import { Log } from "../logs/log";
import { Late } from "../late/late";

import {
  Component,
  useState,
  onWillStart,
  useSubEnv,
  useRef,
  onMounted,
} from "@odoo/owl";

export class Dashboard extends Component {
  setup() {
//    this.state = useState({ absent_employee: 0, present_employee: [], });
    this.state = useState({ absent_employee: 0, present_employee: [], time_off_employee: [], exempt_employee: [] });
    this.orm = useService("orm");
    this.actionService = useService("action");

    useSubEnv({
      config: {
        ...getDefaultConfig(),
        ...this.env.config,
      },
    });



    onWillStart(async () => {

      const permission_employee_data = await this.get_permission_employee();
      this.state.permission_employee = permission_employee_data;

      const exempt_employee_data = await this.get_exempt_employee();
      this.state.exempt_employee = exempt_employee_data;


      const absent_employee_data = await this.get_absent_employee();
      this.state.absent_employee = absent_employee_data;

      const present_employee_data = await this.get_present_employee();
      this.state.present_employee = present_employee_data;

       const time_off_employee_data = await this.get_time_off_employee(); // ⬅️ New
       this.state.time_off_employee = time_off_employee_data;

    });
  }

  async get_exempt_employee() {
  let result = await this.orm.call(
    "sa.attendance.dashboard",
    "get_exempt_employee",
    [[]]
  );
  return result;
}

async get_permission_employee() {
  let result = await this.orm.call(
    "sa.attendance.dashboard",
    "get_permission_employee",
    [[]]
  );
  return result;
}

async get_time_off_employee() {
  let result = await this.orm.call(
    "sa.attendance.dashboard",
    "get_time_off_employee", // ⬅️ Your backend method name
    [[]]
  );
  return result;
}



  async get_absent_employee() {
    let result = await this.orm.call(
      "sa.attendance.dashboard",
      "get_absent_employee",
      [[]]
    );
    return result;
  }

  async get_present_employee() {
    let result = await this.orm.call(
      "sa.attendance.dashboard",
      "get_present_employee",
      [[]]
    );
    return result;
  }

  open_total_employee() {
    const action = this.env.services.action;
    action.doAction({
      type: "ir.actions.act_window",
      name: "Employee",
      res_model: "hr.employee",
      domain: [],
      // context: { search_default_type_company: 1 },
      views: [
        [false, "kanban"],
        [false, "list"],
        [false, "form"],
      ],
      view_mode: "list,form",
      target: "current",
    });
  }

open_permission_employee() {
  const action = this.env.services.action;
  action.doAction({
    type: "ir.actions.act_window",
    name: "Permission Employees",
    res_model: "hr.employee",
    domain: [["id", "in", this.state.permission_employee[1]]],  // Adjust this line as per your actual field name
    views: [
      [false, "kanban"],
      [false, "list"],
      [false, "form"],
    ],
    view_mode: "list,form",
    target: "current",
  });
}


open_exempt_employee() {
  const action = this.env.services.action;
  action.doAction({
    type: "ir.actions.act_window",
    name: "Exempt Employees",
    res_model: "hr.employee",
    domain: [['exempt_from_attendance', '=', true]],   // Adjust this line as per your actual field name
    views: [
      [false, "kanban"],
      [false, "list"],
      [false, "form"],
    ],
    view_mode: "list,form",
    target: "current",
  });
}

open_time_off_employee() {
  const action = this.env.services.action;
  action.doAction({
    type: "ir.actions.act_window",
    name: "Time Off Employees",
    res_model: "hr.employee",
    domain: [["id", "in", this.state.time_off_employee[1]]],
    views: [
      [false, "kanban"],
      [false, "list"],
      [false, "form"],
    ],
    view_mode: "list,form",
    target: "current",
  });
}




  open_present_employee() {
    const action = this.env.services.action;
    action.doAction({
      type: "ir.actions.act_window",
      name: "Present Employees",
      res_model: "hr.employee",
      domain:  [["id", "in", this.state.present_employee[1]]],
      // context: { search_default_type_company: 1 },
      views: [
        [false, "kanban"],
        [false, "list"],
        [false, "form"],
      ],
      view_mode: "list,form",
      target: "current",
    });
  }

  open_absent_employee() {
    const action = this.env.services.action;
    action.doAction({
      type: "ir.actions.act_window",
      name: "Absent Employee",
      res_model: "hr.employee",
      domain: [["id", "in", this.state.absent_employee[1]]],
      // context: { search_default_type_company: 1 },
      views: [
        [false, "kanban"],
        [false, "list"],
        [false, "form"],
      ],
      view_mode: "list,form",
      target: "current",
    });
  }


 



}

Dashboard.template = "softatt_attendance.dashboard_template"; // Template name

Dashboard.components = { ChartRenderer , PieChart, Log, Late};

registry
  .category("actions")
  .add("softatt_attendance.attendance_dashboard", Dashboard); // The ir.actions.client tag field value
