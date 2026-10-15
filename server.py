from emails import EmailSender
from hrms import *
from datetime import datetime
from typing import Any, List, Dict, Optional
from mcp.server.fastmcp import FastMCP

# load the env
from dotenv import load_dotenv
load_dotenv()

import os
from utils import seed_services

employee_manager = EmployeeManager()
meeting_manager = MeetingManager()
leave_manager = LeaveManager()
ticket_manager = TicketManager()

seed_services(employee_manager, leave_manager, meeting_manager, ticket_manager)

emailer = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    username=os.getenv("CB_EMAIL"),
    password=os.getenv("CB_EMAIL_PWD"),
    use_tls=True
)

mcp = FastMCP("hr-assist")

@mcp.tool()
def add_employee(emp_name: str, email: str, manager_id: Optional[str] = None) -> str:
    """
    Add a new employee to the HRMS system.
    :param emp_name: Full name of the new employee
    :param email: Email address of the new employee
    :param manager_id: Employee ID of the manager, e.g. "E003" (optional; use get_employee_details to find it)
    :return: Confirmation message that includes the new employee ID
    """
    emp = EmployeeCreate(
        emp_id=employee_manager.get_next_emp_id(),
        name=emp_name,
        manager_id=manager_id,
        email=email
    )
    employee_manager.add_employee(emp)
    _ = leave_manager.employee_leaves[emp.emp_id]
    return f"Employee {emp_name} added successfully with ID {emp.emp_id}."

@mcp.tool()
def get_employee_details(name: str) -> Dict[str, Optional[str]]:
    """
    Get employee details by employee ID (e.g. "E003") or by name (full or partial).
    :param name: Employee ID or name of the employee
    :return: emp_id, name, manager_id (None if the employee has no manager) and email
    """
    query = name.strip()

    # 1) ID
    emp_id = query.upper()
    if emp_id in employee_manager.employees:
        return employee_manager.get_employee_details(emp_id)

    # 2) name
    matches = employee_manager.search_employee_by_name(query)

    if len(matches) == 0:
        raise ValueError(f"No employees found with name or ID '{name}'.")
    if len(matches) > 1:
        options = ", ".join(f"{eid} ({employee_manager.employees[eid]['name']})" for eid in matches)
        raise ValueError(f"Several employees match '{name}': {options}. Please give the full name or the employee ID.")

    return employee_manager.get_employee_details(matches[0])

@mcp.tool()
def send_email(to_emails: List[str], subject: str, body: str, html: bool = False) -> str:
    """
    Send an email.
    :param to_emails: List of recipient email addresses
    :param subject: Subject line
    :param body: Email text
    :param html: True if the body is HTML
    :return: Confirmation message
    """
    emailer.send_email(subject, body, to_emails, from_email=emailer.username, html=html)
    return "Email sent successfully."


@mcp.tool()
def create_ticket(emp_id: str, item: str, reason:str) -> str:
    """
    Create a ticket for buying required items for an employee.
    :param emp_id: Employee ID
    :param item: Item requested (Laptop, ID Card, etc.)
    :param reason: Reason for the request
    :return: Confirmation message
    """
    ticket_req = TicketCreate(emp_id=emp_id, item=item, reason=reason)
    return ticket_manager.create_ticket(ticket_req)

@mcp.tool()
def update_ticket_status(ticket_id: str, status: str) -> str:
    """
    Update the status of a ticket.
    :param ticket_id: Ticket ID
    :param status: New status of the ticket
    :return: Confirmation message
    """
    ticket_status_update = TicketStatusUpdate(status=status)
    return ticket_manager.update_ticket_status(ticket_status_update, ticket_id)

@mcp.tool()
def list_tickets(employee_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List tickets, optionally filtered by employee and/or status.
    :param employee_id: Employee ID (optional)
    :param status: Ticket status: Open, In Progress, Closed or Rejected (optional)
    :return: List of tickets
    """
    return ticket_manager.list_tickets(employee_id=employee_id, status=status)


@mcp.tool()
def schedule_meeting(employee_id: str, meeting_datetime: datetime, topic: str) -> str:
    """
    Schedule a meeting for an employee.
    :param employee_id: Employee ID
    :param meeting_datetime: Date and time of the meeting in python datetime format
    :param topic: Topic of the meeting
    :return: Confirmation message
    """
    meeting_req = MeetingCreate(
        emp_id=employee_id,
        meeting_dt=meeting_datetime,
        topic=topic
    )
    return meeting_manager.schedule_meeting(meeting_req)


@mcp.tool()
def get_meetings(employee_id: str) -> List[Dict[str, Any]]:
    """
    Get the list of meetings scheduled for an employee.
    :param employee_id: Employee ID
    :return: List of meetings
    """
    return meeting_manager.get_meetings(employee_id)


@mcp.tool()
def cancel_meeting(employee_id: str, meeting_datetime: datetime, topic: Optional[str] = None) -> str:
    """
    Cancel a scheduled meeting for an employee.
    :param employee_id: Employee ID
    :param meeting_datetime: Date and time of the meeting in python datetime format
    :param topic: Topic of the meeting (optional)
    :return: Confirmation message
    """
    meeting_req = MeetingCancelRequest(
        emp_id=employee_id,
        meeting_dt=meeting_datetime,
        topic=topic
    )
    return meeting_manager.cancel_meeting(meeting_req)


@mcp.tool()
def get_employee_leave_balance(emp_id: str) -> str:
    """
    Get the leave balance of an employee.
    :param emp_id: Employee ID
    :return: Leave balance message
    """
    return leave_manager.get_leave_balance(emp_id)

@mcp.tool()
def apply_leave(emp_id: str, leave_dates: List[str]) -> str:
    """
    Apply for leave for an employee.
    :param emp_id: Employee ID
    :param leave_dates: List of leave dates in YYYY-MM-DD format
    :return: Leave application status message
    """
    req = LeaveApplyRequest(emp_id=emp_id, leave_dates=leave_dates)
    return leave_manager.apply_leave(req)


@mcp.tool()
def get_leave_history(emp_id: str) -> str:
    """
    Get the leave history of an employee.
    :param emp_id: Employee ID
    :return: Leave history message
    """
    return leave_manager.get_leave_history(emp_id)


@mcp.prompt("onboard_new_employee")
def onboard_new_employee(employee_name: str, manager_name: str, employee_email: str = ""):
    return f"""Onboard a new employee with the following details:
    - Name: {employee_name}
    - Manager Name: {manager_name}
    - Employee email: {employee_email or "(not given - ask the user)"}
    Steps to follow:
    - Look up the manager with get_employee_details to get the manager's employee ID and email.
    - Add the employee to the HRMS system (add_employee) with that manager ID; note the new employee ID from the reply.
    - Send a welcome email to the employee with their login details.
    - Notify the manager about the new employee's onboarding by email.
    - Raise tickets for a new laptop, id card, and other necessary equipment using the new employee ID.
    - Schedule an introductory meeting between the employee and the manager (use the next business day at 10:00 if no time is given).
    """


if __name__ == "__main__":
    mcp.run(transport="stdio")
