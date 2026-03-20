/**
 * HealVN × OpenClaw Integration
 * Connects AI Hana Wellness Advisor to 22+ messaging channels
 * via OpenClaw (https://github.com/openclaw/openclaw)
 *
 * Channel support: Zalo, WhatsApp, Telegram, Slack, Discord,
 * iMessage, Signal, LINE, Mattermost, Microsoft Teams, WebChat + more
 */

// ─── OPENCLAW SKILL CONFIG ────────────────────────────────────────
// Place this file in your OpenClaw workspace/skills directory
// Then run: openclaw onboard → enable healvn skill

const HEALVN_SKILL = {
  name: "healvn",
  version: "1.0.0",
  description: "HealVN Wellness Advisor — helps users discover real Vietnam havens and book retreats",
  author: "HealVN Team",
  channels: ["zalo", "zalo_personal", "whatsapp", "telegram", "discord", "slack", "webchat"],
};

// ─── HANA AI AGENT DEFINITION ─────────────────────────────────────
const HANA_AGENT = {
  name: "Hana",
  emoji: "🌿",
  persona: `You are Hana, HealVN's AI Wellness Advisor.
You help users discover real, verified havens and nature lifestyle experiences in Vietnam.
You are warm, empathetic, and knowledgeable about Vietnamese wellness traditions.

Core capabilities:
- Assess user's stress level, physical state, and wellness goals
- Match Vietnam's diverse nature (coast, highland, forest, cultural) to user needs
- Build personalized day-by-day wellness journey itineraries
- Recommend verified retreats from HealVN's 1,247+ listings
- Assist with booking via ERPNext API

Always respond in the user's language (Vietnamese or English).
For Vietnamese users: warm, personal tone. For international: professional and trust-building.`,

  // System prompt injected into every conversation
  systemPrompt: `You have access to HealVN's verified retreat database via API.
When a user asks about retreats, call get_retreats() with appropriate filters.
When ready to book, call create_booking() with user details.
Always highlight the 7-layer verification trust badge for retreat recommendations.

API base: ${process.env.HEALVN_API_URL || "http://localhost:8080"}`,
};

// ─── OPENCLAW TOOL DEFINITIONS ────────────────────────────────────
// These tools are exposed to the AI agent via OpenClaw's tool registry

const HEALVN_TOOLS = [
  {
    name: "get_retreats",
    description: "Search verified retreats from HealVN marketplace",
    parameters: {
      category: { type: "string", enum: ["Luxury", "Eco", "Yoga", "Detox", "Spa", "Cultural", "Budget"], optional: true },
      location: { type: "string", description: "Province or city name", optional: true },
      max_price: { type: "number", description: "Max price per person in USD", optional: true },
      duration_days: { type: "number", optional: true },
      stress_level: { type: "number", min: 1, max: 10, optional: true },
    },
    handler: async (params, ctx) => {
      const url = new URL(`${process.env.HEALVN_API_URL}/api/method/healvn.api.get_retreats`);
      Object.entries(params).forEach(([k, v]) => v !== undefined && url.searchParams.set(k, v));
      const res = await fetch(url);
      const data = await res.json();
      return data.message?.retreats || [];
    },
  },

  {
    name: "ai_recommend",
    description: "Get AI-powered retreat recommendations based on wellness profile",
    parameters: {
      stress_level: { type: "number", min: 1, max: 10 },
      budget: { type: "number", description: "Budget per person in USD" },
      duration_days: { type: "number" },
      preferences: { type: "string", description: "Comma-separated: beach, mountain, yoga, detox, cultural", optional: true },
    },
    handler: async (params, ctx) => {
      const res = await fetch(`${process.env.HEALVN_API_URL}/api/method/healvn.api.ai_recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      return data.message?.recommendations || [];
    },
  },

  {
    name: "check_availability",
    description: "Check retreat availability for specific dates",
    parameters: {
      retreat_id: { type: "string" },
      check_in: { type: "string", format: "YYYY-MM-DD" },
      check_out: { type: "string", format: "YYYY-MM-DD" },
    },
    handler: async (params, ctx) => {
      const url = new URL(`${process.env.HEALVN_API_URL}/api/method/healvn.api.check_availability`);
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
      const res = await fetch(url);
      return (await res.json()).message;
    },
  },

  {
    name: "create_wellness_journey",
    description: "Generate a full day-by-day wellness journey itinerary for the user",
    parameters: {
      retreat_id: { type: "string" },
      stress_level: { type: "number", min: 1, max: 10 },
      focus_areas: { type: "string", description: "e.g. mental, physical, spiritual, detox" },
      duration_days: { type: "number" },
    },
    handler: async (params, ctx) => {
      const res = await fetch(`${process.env.HEALVN_API_URL}/api/method/healvn.api.create_wellness_journey`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...params, user_id: ctx.userId }),
      });
      return (await res.json()).message;
    },
  },

  {
    name: "create_booking",
    description: "Create a retreat booking for the user",
    parameters: {
      retreat: { type: "string", description: "Retreat document name, e.g. RET-2025-0001" },
      guest_name: { type: "string" },
      guest_email: { type: "string" },
      guest_phone: { type: "string", optional: true },
      check_in: { type: "string", format: "YYYY-MM-DD" },
      check_out: { type: "string", format: "YYYY-MM-DD" },
      num_guests: { type: "number", default: 1 },
    },
    handler: async (params, ctx) => {
      const res = await fetch(`${process.env.HEALVN_API_URL}/api/method/healvn.api.create_booking`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `token ${process.env.HEALVN_API_KEY}:${process.env.HEALVN_API_SECRET}`,
        },
        body: JSON.stringify(params),
      });
      return (await res.json()).message;
    },
  },
];

// ─── CHANNEL-SPECIFIC MESSAGE FORMATTERS ─────────────────────────

const formatRetreatForChannel = (retreat, channel) => {
  const trust = "✅ 7-Layer Verified";
  const price = `$${retreat.price_per_person}/person`;
  const rating = `⭐ ${retreat.average_rating}`;

  if (channel === "zalo" || channel === "zalo_personal") {
    // Zalo supports rich cards
    return {
      type: "card",
      title: `🌿 ${retreat.retreat_name}`,
      subtitle: `📍 ${retreat.location} · ${retreat.duration_days} ngày`,
      body: `${trust} · ${price} · ${rating}`,
      buttons: [
        { label: "Xem Chi Tiết", action: `https://healvn.com/retreats/${retreat.name}` },
        { label: "📅 Book Ngay", action: "postback", data: `book:${retreat.name}` },
      ],
    };
  }

  if (channel === "telegram") {
    return {
      type: "inline_keyboard",
      text: `🌿 *${retreat.retreat_name}*\n📍 ${retreat.location}\n${trust} · ${price} · ${rating}`,
      keyboard: [[
        { text: "Book Now →", url: `https://healvn.com/retreats/${retreat.name}` },
      ]],
    };
  }

  if (channel === "slack" || channel === "discord") {
    return {
      type: "block",
      blocks: [
        { type: "section", text: { type: "mrkdwn", text: `🌿 *${retreat.retreat_name}* — 📍 ${retreat.location}` } },
        { type: "context", elements: [{ type: "mrkdwn", text: `${trust} · ${price} · ${rating}` }] },
        { type: "actions", elements: [{ type: "button", text: { type: "plain_text", text: "Book Retreat →" }, url: `https://healvn.com/retreats/${retreat.name}` }] },
      ],
    };
  }

  // Default text fallback (WhatsApp, Signal, iMessage, etc.)
  return `🌿 *${retreat.retreat_name}*\n📍 ${retreat.location} · ${retreat.duration_days} days\n${trust}\n💰 ${price} · ${rating}\n\n👉 healvn.com/retreats/${retreat.name}`;
};

// ─── OPENCLAW SKILL EXPORT ────────────────────────────────────────
module.exports = {
  skill: HEALVN_SKILL,
  agent: HANA_AGENT,
  tools: HEALVN_TOOLS,
  formatters: { formatRetreatForChannel },
};

/**
 * SETUP INSTRUCTIONS
 * ──────────────────
 * 1. Install OpenClaw: npx openclaw onboard
 * 2. Copy this file to: ~/.openclaw/workspace/skills/healvn/
 * 3. Set environment variables in .env:
 *      HEALVN_API_URL=http://localhost:8080
 *      HEALVN_API_KEY=your_api_key
 *      HEALVN_API_SECRET=your_api_secret
 * 4. Enable channels in OpenClaw config (zalo, whatsapp, telegram…)
 * 5. Run: openclaw dev
 *
 * Hana will now respond on all your configured channels! 🌿
 *
 * Docs: https://docs.openclaw.ai/tools/skills
 */
