# PUBLIC Schema ERD

```mermaid
erDiagram
    public__employee_trainings {
        integer id [PK]
        integer employee_id [FK]
        string module_id [FK]
        string status
        float score
        datetime completed_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    public__employee_trainings ||--o| hr__employees : has
    public__employee_trainings ||--o| hr__training_modules : has
    public__payroll_records {
        integer id [PK]
        string country_code
        integer employee_id [FK]
        numeric net_pay
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    public__payroll_records ||--o| hr__employees : has
```