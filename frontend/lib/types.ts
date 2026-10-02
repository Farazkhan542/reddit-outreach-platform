import type { Role } from "./api";

export interface User {
  id: string;
  org_id: string;
  email: string;
  display_name: string | null;
  role: Role;
  is_active: boolean;
}

export interface TenantConfig {
  niche: string;
  product_description: string;
  subreddits: string[];
  keywords: string[];
  personas: string[];
  tone: string;
  distribution_strategy: "round_robin" | "least_recently_active" | "manual_claim";
  intent_threshold: number;
  poll_interval_minutes: number;
  is_live: boolean;
}

export interface Lead {
  id: string;
  subreddit: string;
  author: string;
  title: string | null;
  body: string;
  permalink: string;
  intent_score: number | null;
  intent_reasoning: string | null;
  extracted_needs: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface Reply {
  id: string;
  lead_id: string;
  draft_body: string;
  final_body: string | null;
  status: "pending_review" | "approved" | "rejected" | "posted";
  posted_url: string | null;
  created_at: string;
}

export interface ApprovalApplication {
  app_name: string;
  company_name: string;
  website_url: string;
  privacy_policy_url: string;
  contact_email: string;
  reddit_username: string;
  reddit_account_age_days: number;
  is_commercial: boolean;
  data_retention_days: number;
  steps_done: string[];
  status: "not_started" | "submitted" | "approved" | "denied";
  reviewer_notes: string | null;
  submitted_at: string | null;
}

export interface CheckItem {
  id: string;
  title: string;
  status: "pass" | "warn" | "fail";
  detail: string;
  fix: string | null;
}

export interface CheckResult {
  ready: boolean;
  score: number;
  items: CheckItem[];
}

export interface ApprovalGuide {
  application: ApprovalApplication;
  steps: { id: string; title: string; body: string; link: string | null; link_label: string | null }[];
  check: CheckResult;
  request_text: string;
}

export interface Analytics {
  leads_total: number;
  leads_qualified: number;
  replies_pending: number;
  replies_posted: number;
  approval_rate: number | null;
}
