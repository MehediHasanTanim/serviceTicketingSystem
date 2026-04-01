# Hotel Operations Suite Feature List (Cited + Checklist)

This document lists parity-level features based on public information about Amadeus HotSOS and HubOS, with citations and a requirements-style checklist.

## Cited Feature List

Core Platform (Cross-Department)
- Role-based access for staff, supervisors, and managers with mobile access. [S1]
- Centralized multi-department platform covering housekeeping, maintenance, guest experience, compliance/risk, projects, F&B, corporate, energy/sustainability, and guest communication. [S11] [S12]
- Mobile support with offline functionality for operations teams. [S6] [S11]
- Business intelligence, dashboards, and reporting for operational performance. [S11]
- PMS integration and broader system integrations. [S11]

Service Orders / Ticketing (HotSOS-Parity Core)
- Service order creation, detailed order view, and assignment visibility. [S1]
- Order lifecycle statuses including start, stop, complete, defer, and void. [S5]
- Priority levels on service orders. [S1]
- Multiple service order types: standard tickets, preventive maintenance (PM), inspections, incidents, rounds, delivery, transportation. [S3]
- Attachments and remarks on orders. [S1]
- Cost tracking for parts, labor, and guest compensation/recovery. [S1]

Inspections
- Inspection orders with step-based workflows and pass/fail/N/A responses. [S4]
- Inspection scoring with saved history for reporting. [S4]
- Inspections applicable to guestrooms, public spaces, and staff performance. [S4]

Housekeeping
- Automated daily task assignment based on occupancy and priorities. [S6]
- Real-time room status updates synced with PMS. [S6]
- Mobile housekeeping workflow with offline capability. [S6]
- Housekeeping performance analytics and KPI tracking. [S6]

Maintenance
- Corrective and preventive maintenance coverage. [S11] [S12]
- Preventive maintenance scheduling and task generation. [S7]
- Custom checklists and maintenance logbook. [S7]
- Offline inspections for maintenance workflows. [S7]
- Asset/equipment management with QR support. [S7]

Guest Experience (Complaints & Follow-Up)
- Centralized guest complaint and issue overview. [S8]
- Real-time incident notifications for guest issues. [S8]
- Mobile complaint management. [S8]
- Guest follow-up workflow before checkout. [S8]
- Guest experience analytics and weekly insights/reports. [S8]

Guest Communication (Guest-Facing Requests)
- Guest web app for service requests (housekeeping, reservations, incident reporting). [S9]
- Requests routed to the responsible teams and staff. [S9]
- Request tracking to improve response times and satisfaction. [S9]

Risk & Compliance
- Governance, risk, and compliance management with centralized oversight. [S10]
- Compliance dashboards across buildings or hotel groups. [S10]
- Legal, contract, and audit management coverage. [S10]

Projects
- Snagging lists and technical audits for projects. [S12]

Food & Beverage
- Breakfast tracking and outlet coordination. [S12]

Corporate
- Contract, supplier, order, and CAPEX management at corporate level. [S12]

Energy & Sustainability
- Energy KPI analysis for efficiency and decision support. [S12]

## Requirements-Style Checklist

Core Platform
- [ ] Implement role-based access and permissions, including mobile access. [S1]
- [ ] Provide a unified platform spanning housekeeping, maintenance, guest experience, compliance/risk, projects, F&B, corporate, energy/sustainability, and guest communication. [S11] [S12]
- [ ] Support mobile workflows with offline mode. [S6] [S11]
- [ ] Provide BI dashboards and reporting. [S11]
- [ ] Integrate with PMS and other hotel systems. [S11]

Service Orders / Ticketing
- [ ] Create and manage service orders with detailed views and assignment handling. [S1]
- [ ] Support lifecycle statuses: start, stop, complete, defer, void. [S5]
- [ ] Allow priority levels on orders. [S1]
- [ ] Support order types: standard, PM, inspections, incidents, rounds, delivery, transportation. [S3]
- [ ] Support attachments and remarks. [S1]
- [ ] Track parts, labor, and guest compensation/recovery costs. [S1]

Inspections
- [ ] Build inspection workflows with step-based pass/fail/N/A responses. [S4]
- [ ] Store inspection scores and history. [S4]
- [ ] Support inspection scopes for guestrooms, public spaces, and staff. [S4]

Housekeeping
- [ ] Automate task assignment using occupancy and priorities. [S6]
- [ ] Sync real-time room statuses with PMS. [S6]
- [ ] Enable mobile housekeeping workflow with offline access. [S6]
- [ ] Track housekeeping KPIs and analytics. [S6]

Maintenance
- [ ] Cover corrective and preventive maintenance. [S11] [S12]
- [ ] Implement PM scheduling and automated task generation. [S7]
- [ ] Provide checklists and maintenance logbook. [S7]
- [ ] Support offline maintenance inspections. [S7]
- [ ] Implement asset/equipment tracking with QR. [S7]

Guest Experience
- [ ] Centralize guest complaints and issues. [S8]
- [ ] Push real-time incident notifications. [S8]
- [ ] Provide mobile complaint management. [S8]
- [ ] Enable guest follow-up before checkout. [S8]
- [ ] Provide analytics and weekly insights. [S8]

Guest Communication
- [ ] Provide a guest web app for service requests. [S9]
- [ ] Route requests to responsible teams and staff. [S9]
- [ ] Track request progress and outcomes. [S9]

Risk & Compliance
- [ ] Provide governance, risk, and compliance management. [S10]
- [ ] Provide compliance dashboards across properties. [S10]
- [ ] Support legal, contract, and audit management. [S10]

Projects
- [ ] Support snagging lists and technical audits. [S12]

Food & Beverage
- [ ] Track breakfast operations and outlet coordination. [S12]

Corporate
- [ ] Manage contracts, suppliers, orders, and CAPEX. [S12]

Energy & Sustainability
- [ ] Provide energy KPI analysis for efficiency decisions. [S12]

## Sources

- [S1] Amadeus HotSOS Service Order Details: https://help.amadeus-hospitality.com/operations/service-optimization/hotsos/content/service-order-details.html
- [S3] Amadeus HotSOS Issues and Issue Types: https://help.amadeus-hospitality.com/operations/service-optimization/hotsos/content/issue-details.html
- [S4] Amadeus HotSOS Perform an Inspection: https://help.amadeus-hospitality.com/operations/service-optimization/hotsos/content/service-order-inspection.html
- [S5] Amadeus HotSOS Respond to Service Orders: https://help.amadeus-hospitality.com/operations/service-optimization/hotsos/content/service-orders-respond.html
- [S6] HubOS Housekeeping: https://hubos.com/housekeeping/
- [S7] HubOS Maintenance: https://hubos.com/maintenance/
- [S8] HubOS Guest Experience: https://hubos.com/guest-experience/
- [S9] HubOS Guest in Touch: https://hubos.com/guest-in-touch/
- [S10] HubOS Risk & Compliance: https://hubos.com/risk-compliance/
- [S11] HubOS Platform Overview: https://hubos.com/
- [S12] HubOS 2025 Web (modules list): https://hubos.com/2025-web/
