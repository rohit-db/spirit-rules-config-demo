export interface RuleHeader {
  id: string;
  start_date: string;
  end_date: string;
  cost_category: string;
  rate_category: string | null;
  category: string | null;
  account_group: string | null;
  groupby_costcenter: boolean;
  groupby_account: boolean;
  fixed_variable_pct_split: number | null;
  fixed_variable_type: string | null;
  status: "draft" | "in_review" | "approved" | "archived";
  version: number;
  cloned_from_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface RuleLine {
  id: string;
  header_id: string;
  account_number: string;
  account_name: string | null;
  stat_type: string;
  proration_rate: number;
  effective_date: string | null;
  notes: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  header_id: string;
  action: string;
  changed_by: string;
  changed_at: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
}
