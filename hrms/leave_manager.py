from collections import defaultdict
from datetime import date
from typing import Dict

from hrms.schemas import LeaveApplyRequest


class LeaveManager:
    def __init__(self):
        self.employee_leaves: Dict[str, Dict] = defaultdict(
            lambda: {"balance": 20, "history": []}
        )

    def get_leave_balance(self, employee_id: str) -> str:
        data = self.employee_leaves.get(employee_id)
        if data:
            return f"{employee_id} has {data['balance']} leave days remaining."
        return "Employee ID not found."

    def apply_leave(self, req: LeaveApplyRequest) -> str:
        employee_id = req.emp_id
        if employee_id not in self.employee_leaves:
            return "Employee ID not found."
        requested = len(req.leave_dates)
        available = self.employee_leaves[employee_id]["balance"]
        if available < requested:
            return f"Insufficient leave balance: requested {requested}, available {available}."
        self.employee_leaves[employee_id]["balance"] -= requested

        # store entries in the same format as the seeded data (dicts with a real date)
        history = self.employee_leaves[employee_id]["history"]
        request_id = max((h.get("request_id", 0) for h in history), default=0) + 1
        for d in req.leave_dates:
            history.append({
                "history_id": len(history) + 1,
                "emp_id": employee_id,
                "leave_date": d,
                "request_id": request_id,
            })
        return (f"Leave applied for {requested} day(s). Remaining balance: "
                f"{self.employee_leaves[employee_id]['balance']}")

    def get_leave_history(self, employee_id: str) -> str:
        data = self.employee_leaves.get(employee_id)
        if not data:
            return "Employee ID not found."
        dates = []
        for record in data["history"]:
            d = record["leave_date"]
            if isinstance(d, str):                       # accept ISO strings as well as date objects
                d = date.fromisoformat(d)
            dates.append(d.strftime("%B %d, %Y"))
        if not dates:
            return f"No leave taken by {employee_id}."
        return f"Leave history for {employee_id}: {', '.join(dates)}."

if __name__ == "__main__":
    lm = LeaveManager()
    print(lm.get_leave_history("E004"))