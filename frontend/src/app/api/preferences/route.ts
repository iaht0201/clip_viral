import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    monetization_enabled: false,
    can_create_task: true,
    plan: "free",
    usage_count: 0,
    usage_limit: 10,
    subscription_status: "inactive"
  });
}
