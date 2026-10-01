# HR Schema ERD

```mermaid
erDiagram
    hr__hr.alumni_networks {
        integer id [PK]
        integer employee_id [UK, FK]
        string status
        datetime granted_at
        datetime eligibility_expires_at
        text notes
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.alumni_networks ||--o| hr__employees : has
    hr__hr.coi_reports {
        integer id [PK]
        integer employee_id [FK]
        string related_person_name
        string relation_type
        boolean is_internal
        integer internal_employee_id [FK]
        string risk_level
        boolean is_approved
        integer approved_by_id [FK]
        datetime approved_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.coi_reports ||--o| hr__employees : has
    hr__hr.coi_reports ||--o| hr__employees : has
    hr__hr.coi_reports ||--o| accounts__users : has
    hr__hr.disciplinary_cases {
        integer id [PK]
        integer employee_id [FK]
        string employee_name
        string stage
        text description
        datetime issued_at
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.disciplinary_cases ||--o| hr__employees : has
    hr__hr.dynamic_qr_sessions {
        integer id [PK]
        integer employee_id [FK]
        string qr_token [UK]
        datetime expires_at
        datetime used_at
        string ip_address
        string user_agent
        string device_fingerprint
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.dynamic_qr_sessions ||--o| hr__employees : has
    hr__hr.employee_activity_logs {
        integer id [PK]
        integer actor_employee_id [FK]
        string action
        string entity_type
        integer entity_id
        json metadata_json
        string ip_address
        string device_fingerprint
        string country_code
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    hr__hr.employee_activity_logs ||--o| hr__employees : has
    hr__hr.employee_addresses {
        integer id [PK]
        integer employee_id [FK]
        string address_type
        string street
        string city
        string state
        string postal_code
        string country_code [FK]
        boolean is_primary
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    hr__hr.employee_addresses ||--o| hr__employees : has
    hr__hr.employee_addresses ||--o| country__country_configs : has
    hr__hr.employee_assets {
        integer id [PK]
        integer employee_id [FK]
        string asset_type
        string asset_id
        string serial_no
        datetime assigned_at
        datetime returned_at
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_assets ||--o| hr__employees : has
    hr__hr.employee_attendances {
        integer id [PK]
        integer employee_id [FK]
        date record_date
        datetime scan_in_time
        datetime scan_out_time
        string scan_type
        float location_lat
        float location_long
        string device_fingerprint
        boolean is_anomaly
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_attendances ||--o| hr__employees : has
    hr__hr.employee_biometrics {
        integer id [PK]
        integer employee_id [UK, FK]
        string fingerprint_hash
        text face_encoding
        string biometric_type
        datetime enrolled_at
        boolean is_active
        boolean is_deleted
        string country_code
    }
    hr__hr.employee_biometrics ||--o| hr__employees : has
    hr__hr.employee_certifications {
        integer id [PK]
        integer employee_id [FK]
        string cert_type
        string cert_name
        date issued_date
        date expiry_date
        boolean is_valid
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_certifications ||--o| hr__employees : has
    hr__hr.employee_dependents {
        integer id [PK]
        integer employee_id [FK]
        string name
        string relation
        date dob
        boolean is_insured
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_dependents ||--o| hr__employees : has
    hr__hr.employee_documents {
        integer id [PK]
        integer employee_id [FK]
        string doc_type
        string file_url
        date expiry_date
        integer verified_by_id [FK]
        datetime verified_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_documents ||--o| hr__employees : has
    hr__hr.employee_documents ||--o| accounts__users : has
    hr__hr.employee_leave_ledgers {
        integer id [PK]
        integer employee_id [FK]
        string leave_type
        integer year
        integer allocated_days
        integer used_days
        integer carried_forward
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_leave_ledgers ||--o| hr__employees : has
    hr__hr.employee_leave_requests {
        integer id [PK]
        integer employee_id [FK]
        string leave_type
        date start_date
        date end_date
        integer days_requested
        string status
        integer approved_by_id [FK]
        datetime approved_at
        text rejection_reason
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_leave_requests ||--o| hr__employees : has
    hr__hr.employee_leave_requests ||--o| accounts__users : has
    hr__hr.employee_relations {
        integer id [PK]
        integer employee_id [FK]
        string related_person_name
        string relation_type
        boolean is_internal_employee
        integer internal_employee_id [FK]
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_relations ||--o| hr__employees : has
    hr__hr.employee_relations ||--o| hr__employees : has
    hr__hr.employee_risk_scores {
        integer id [PK]
        integer employee_id [FK]
        date assessment_date
        float score
        string risk_level
        json factors
        text notes
        string country_code
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    hr__hr.employee_risk_scores ||--o| hr__employees : has
    hr__hr.employee_roles {
        integer id [PK]
        string role_name [UK]
        json permissions
        integer authority_level
        boolean can_approve_leave
        boolean can_approve_expense
        boolean can_manage_users
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
    }
    hr__hr.employee_shift_rosters {
        integer id [PK]
        integer employee_id [FK]
        date shift_date
        time start_time
        time end_time
        string shift_type
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_shift_rosters ||--o| hr__employees : has
    hr__hr.employee_travel_requests {
        integer id [PK]
        integer employee_id [FK]
        string destination_country
        date start_date
        date end_date
        string purpose
        string status
        integer approved_by_id [FK]
        datetime approved_at
        json per_diem_json
        numeric total_cost
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_travel_requests ||--o| hr__employees : has
    hr__hr.employee_travel_requests ||--o| accounts__users : has
    hr__hr.employee_work_logs {
        integer id [PK]
        integer employee_id [FK]
        date record_date
        numeric hours_worked
        text task_description
        float location_lat
        float location_long
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.employee_work_logs ||--o| hr__employees : has
    hr__hr.employees {
        integer id [PK]
        integer user_id [UK, FK]
        string employee_code [UK]
        integer office_id [FK]
        string department
        string position
        string employment_type
        string employment_status
        numeric salary
        string currency
        string country_code [FK]
        date hire_date
        date termination_date
        boolean is_verified
        string gender
        integer years_of_experience
        integer performance_score
        string education_level
        text notes
        integer reporting_manager_id [FK]
        integer hiring_manager_id [FK]
        integer authority_level
        integer org_unit_id [FK]
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    hr__hr.employees ||--o| accounts__users : has
    hr__hr.employees ||--o| hr__offices : has
    hr__hr.employees ||--o| country__country_configs : has
    hr__hr.employees ||--o| hr__employees : has
    hr__hr.employees ||--o| accounts__users : has
    hr__hr.employees ||--o| hr__org_units : has
    hr__hr.geo_fence_logs {
        integer id [PK]
        integer employee_id [FK]
        float latitude
        float longitude
        integer accuracy_meters
        datetime scanned_at
        boolean is_within_fence
        boolean is_deleted
        string country_code
    }
    hr__hr.geo_fence_logs ||--o| hr__employees : has
    hr__hr.offboarding_cases {
        integer id [PK]
        integer employee_id [FK]
        string employee_name
        string reason
        string status
        datetime initiated_at
        datetime completed_at
        text notes
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.offboarding_cases ||--o| hr__employees : has
    hr__hr.offices {
        integer id [PK]
        string name
        string city
        float latitude
        float longitude
        integer geo_fence_radius_meters
        text address
        string phone
        string email
        boolean is_active
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
    }
    hr__hr.onboarding_pipelines {
        integer id [PK]
        integer user_id [FK]
        string pipeline_type
        string status
        integer current_step
        json steps_data
        datetime started_at
        datetime completed_at
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    hr__hr.onboarding_pipelines ||--o| accounts__users : has
    hr__hr.onboarding_steps {
        integer id [PK]
        integer pipeline_id [FK]
        string step_name
        string status
        json data
        datetime started_at
        datetime completed_at
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    hr__hr.onboarding_steps ||--o| hr__onboarding_pipelines : has
    hr__hr.org_units {
        integer id [PK]
        string name
        integer parent_id [FK]
        string country_code
        integer level
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    hr__hr.org_units ||--o| hr__org_units : has
    hr__hr.physical_id_cards {
        integer id [PK]
        integer employee_id [UK, FK]
        string card_number [UK]
        datetime issued_at
        datetime expires_at
        boolean is_revoked
        datetime revoked_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    hr__hr.physical_id_cards ||--o| hr__employees : has
    hr__hr.shift_handover_sessions {
        integer id [PK]
        string country_code [FK]
        integer outgoing_employee_id [FK]
        integer incoming_employee_id [FK]
        datetime shift_date
        text notes
        string status
        datetime acknowledged_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    hr__hr.shift_handover_sessions ||--o| country__country_configs : has
    hr__hr.shift_handover_sessions ||--o| hr__employees : has
    hr__hr.shift_handover_sessions ||--o| hr__employees : has
    hr__hr.shift_handover_tasks {
        integer id [PK]
        integer session_id [FK]
        text description
        string priority
        string status
        integer assigned_to_id [FK]
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    hr__hr.shift_handover_tasks ||--o| hr__shift_handover_sessions : has
    hr__hr.shift_handover_tasks ||--o| accounts__users : has
    hr__hr.training_modules {
        string module_id [PK]
        string title
        text description
        string required_for_role
        integer duration_minutes
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
```