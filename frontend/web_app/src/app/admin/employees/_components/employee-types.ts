export type EmployeeTab =
  | "directory"
  | "offices"
  | "attendance"
  | "leaves"
  | "shifts"
  | "iam"
  | "payroll"
  | "documents"
  | "coi"
  | "audit"
  | "communications"
  | "addresses"
  | "performance"
  | "disciplinary"
  | "hse"
  | "alumni"
  | "insurance"
  | "dei";

export interface Employee {
  id: number;
  employee_code: string;
  user_id: number | null;
  full_name?: string;
  name?: string;
  email?: string;
  phone?: string | null;
  office?: string | null;
  office_id?: number | null;
  department: string | null;
  position: string | null;
  employment_type: string;
  employment_status: string;
  salary: number | null;
  currency: string;
  country_code?: string | null;
  hire_date: string | null;
  termination_date?: string | null;
  is_verified?: boolean;
  gender?: string | null;
  notes?: string | null;
  created_at?: string;
}

export interface Office {
  id: number;
  name: string;
  country_code: string;
  city?: string;
  latitude?: number | null;
  longitude?: number | null;
  geo_fence_radius?: number | null;
  address?: string | null;
  is_active?: boolean;
}

export interface AttendanceRecord {
  id: number;
  employee_id: number;
  date: string;
  scan_in_time?: string | null;
  scan_out_time?: string | null;
  status: string;
  is_anomaly?: boolean;
  hours_worked?: number | null;
}

export interface LeaveRequest {
  id: number;
  employee_id: number;
  employee_name?: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  days_requested: number;
  status: string;
  approved_by?: number | null;
  notes?: string | null;
}

export interface ShiftRoster {
  id: number;
  employee_id: number;
  employee_name?: string;
  shift_date: string;
  start_time: string;
  end_time: string;
  shift_type: string;
  status: string;
}

export interface CreateEmployeeForm {
  user_id: string;
  employee_code: string;
  office_id: string;
  department: string;
  position: string;
  employment_type: string;
  salary: string;
  currency: string;
  hire_date: string;
  country_code: string;
}

export const EMPTY_FORM: CreateEmployeeForm = {
  user_id: "",
  employee_code: "",
  office_id: "",
  department: "",
  position: "",
  employment_type: "full_time",
  salary: "",
  currency: "OMR",
  hire_date: new Date().toISOString().split("T")[0],
  country_code: "",
};
