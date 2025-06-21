from enum import Enum


class AppointmentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment:
    id: str
    customer_id: str
    date: str
    time: str
    status: AppointmentStatus

    def __init__(
        self, id: str, customer_id: str, date: str, time: str, status: AppointmentStatus
    ):
        self.id = id
        self.customer_id = customer_id
        self.date = date
        self.time = time
        self.status = status

    def to_json(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "date": self.date,
            "time": self.time,
            "status": self.status.value,
        }


class ProviderStore:
    appointments: list[Appointment] = []

    def __init__(self):
        self.appointments = []
        self._initialize_mock_data()

    def _initialize_mock_data(self):
        self.appointments = [
            Appointment(
                "APT-2025-001",
                "CUST-1001",
                "2025-03-20",
                "09:00",
                AppointmentStatus.COMPLETED,
            ),
            Appointment(
                "APT-2025-002",
                "CUST-1001",
                "2025-07-19",
                "09:00",
                AppointmentStatus.CONFIRMED,
            ),
            Appointment(
                "APT-2025-003",
                "CUST-1001",
                "2025-08-25",
                "14:00",
                AppointmentStatus.PENDING,
            ),
            Appointment(
                "APT-2025-004",
                "CUST-1002",
                "2025-07-20",
                "10:30",
                AppointmentStatus.CONFIRMED,
            ),
            Appointment(
                "APT-2025-005",
                "CUST-1002",
                "2025-03-23",
                "13:00",
                AppointmentStatus.CANCELLED,
            ),
            Appointment(
                "APT-2025-006",
                "CUST-1003",
                "2025-07-20",
                "14:00",
                AppointmentStatus.PENDING,
            ),
            Appointment(
                "APT-2025-007",
                "CUST-1003",
                "2025-07-28",
                "11:30",
                AppointmentStatus.PENDING,
            ),
        ]
        self.appointments.extend(self.appointments)

    def add_appointment(self, appointment: Appointment):
        appointment.id = f"APT-2025-00{len(self.appointments) + 1}"
        self.appointments.append(appointment)

    def get_appointments(self, customer_id: str):
        return [
            appointment.to_json()
            for appointment in self.appointments
            if appointment.customer_id == customer_id
        ]

    def get_appointment(self, appointment_id: str):
        appointment = next(
            (
                appointment
                for appointment in self.appointments
                if appointment.id == appointment_id
            ),
            None,
        )
        return appointment if appointment else None

    def update_appointment(self, appointment_id: str, status: AppointmentStatus):
        appointment = self.get_appointment(appointment_id)
        if appointment:
            appointment.status = status


# Initialize the provider store
providerStore = ProviderStore()
