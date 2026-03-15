# Launch Blocker Tracker — Updated 2026-03-16 (Heartbeat #8 consolidated)

> Cross-reference: [Launch Readiness Audit](launch_readiness_audit.md) | [Launch Coordination](launch_coordination.md)

## Overall Launch Readiness: ~48% (marketing near saturation — blocked on Board/Engineering)

### Progress Since Last Audit

| Area | Previous | Current | Change |
|------|----------|---------|--------|
| Marketing Content | 95% | 99% | +4% (Blog #4 chatbot tutorial, Migration Guide Dev.to/Medium adapt, KOL email sequences, Developer Advocate kit, Week 8 tweets) |
| Product / Tech | 40% | 40% | No change — KYD-22 blocked, KYD-35 blocked |
| Visual Assets | 0% | 0% | No change — **blocked on quality dashboard** |
| Social Channels | 0% | 0% | No change — **blocked on Board action** |
| SEO Infrastructure | 0% | 0% | No change — **blocked on Engineering** |

---

## P0 Blockers (Must resolve before launch)

### 1. Twitter @OpenClade Account
- **Owner:** Board (human action required)
- **Status:** NOT STARTED
- **Impact:** 80 tweets ready (Week 1-8), KOL outreach planned, all social content references this handle
- **Action:** Board needs to register @OpenClade on Twitter/X
- **Dependencies:** None
- **Days blocked:** 8+ heartbeats flagged — ESCALATING

### 2. Discord Server
- **Owner:** Board (human action required)
- **Status:** NOT STARTED
- **Impact:** Community plans ready, miner recruitment depends on Discord for support
- **Action:** Board needs to create Discord server, CMO will configure channels per community plan
- **Dependencies:** None
- **Days blocked:** 6+ heartbeats flagged

### 3. /blog Route + Sitemap.xml
- **Owner:** Frontend Engineer
- **Status:** NOT STARTED
- **Impact:** 7 blog articles + 4 SEO articles ready but cannot be published. SEO strategy entirely blocked. Dev.to cross-posting also waiting on canonical URLs.
- **Action:** Add `/blog` route in Next.js frontend, generate `sitemap.xml`, configure `robots.txt`
- **Dependencies:** Engineering bandwidth
- **Estimated effort:** 4-8 hours
- **Days blocked:** 5+ heartbeats flagged — ESCALATING

### 4. Gallery Images (5 PH required)
- **Owner:** Design / Engineering collaboration
- **Status:** NOT STARTED
- **Impact:** ProductHunt listing requires minimum 3 gallery images, recommended 5
- **Required images:**
  1. Price comparison graphic (OpenClade vs Official)
  2. Code screenshot (1-line migration)
  3. Architecture diagram (3-party model)
  4. Quality dashboard screenshot
  5. Miner earnings visualization
- **Dependencies:** Quality dashboard needs to exist (#6 below)
- **Estimated effort:** 1-2 days

### 5. Product Demo Video (60s)
- **Owner:** Engineering / CEO
- **Status:** NOT STARTED
- **Impact:** PH listings with videos rank significantly higher. Also needed for KOL outreach.
- **Action:** Record a 60-second screencast showing: signup → get API key → run code → see response → show cost savings
- **Dependencies:** Working production instance
- **Estimated effort:** 2-4 hours (recording + editing)

### 6. Public Quality Dashboard
- **Owner:** Frontend + Backend Engineering
- **Status:** NOT STARTED
- **Impact:** Referenced in social content, KOL outreach, blog articles, competitive positioning. Core trust-building asset.
- **Action:** Create a public-facing page showing real-time quality scores, latency metrics, uptime
- **Dependencies:** Monitoring system (DONE — Grafana + Prometheus deployed), frontend route
- **Estimated effort:** 1-2 days

---

## P1 Items (Should resolve before launch)

### 7. Google Search Console Verification
- **Owner:** Board
- **Status:** NOT STARTED
- **Dependencies:** Domain DNS access
- **Action:** Verify openclade.com domain, submit sitemap

### 8. Email Infrastructure (Resend/Loops/Postmark)
- **Owner:** Backend Engineering
- **Status:** NOT STARTED
- **Impact:** Email marketing strategy and 5-email launch sequence ready, no sending capability
- **Dependencies:** Domain DNS (SPF/DKIM/DMARC)

### 9. Referral System
- **Owner:** Backend Engineering
- **Status:** NOT STARTED
- **Impact:** KOL partnership model includes referral commissions
- **Dependencies:** User accounts system

### 10. UTM Parameter Tracking
- **Owner:** Backend Engineering
- **Status:** NOT STARTED
- **Impact:** Cannot measure channel attribution without UTM storage on signup
- **Dependencies:** Registration flow

---

## Recently Resolved Items

| Item | Resolved In | Notes |
|------|------------|-------|
| Security audit (OWASP Top 10) | KYD-21 | sr25519 verification, CORS, CSP, httpOnly cookies |
| Monitoring + alerting | KYD-27 / KYD-43 | Prometheus, Grafana, Slack alerts live |
| Frontend English portal | KYD-42 | Landing page updated |
| Bittensor v10 migration | KYD-22 | Testnet verified |
| Production infrastructure | KYD-33 | Redis HA, PostgreSQL replica |
| Performance optimization | KYD-51 | Core Web Vitals improvements |
| Rollback SOP | KYD-53 | Zero-downtime rollback documented |
| On-call handbook | KYD-56 | 7 runbooks ready |

---

## Recommended Launch Sequence

Given current blockers, here's the suggested priority order to reach 80% readiness:

1. **Board immediately:** Create Twitter + Discord (30 min total, unblocks all social/community work)
2. **Engineering Day 1:** `/blog` route + sitemap (4-8h, unblocks all SEO content)
3. **Engineering Day 1-2:** Public quality dashboard (unblocks gallery images + trust building)
4. **Engineering Day 2:** Gallery images using real dashboard data
5. **CEO/Eng Day 2:** Record demo video (2-4h)
6. **Board Day 2:** Google Search Console verification

**Earliest possible launch date:** T+5 days from Board action on #1-2.

---

## CMO Marketing Content Status

| Category | Files | Items | Status |
|----------|-------|-------|--------|
| GTM Strategy | 1 | — | Done |
| Twitter Content | 8 | 80 tweets | Week 1-8 ready |
| Community Ops | 1 | — | Done |
| Miner Recruitment | 2 | — | Done |
| Landing Page Review | 1 | — | Done |
| Blog Articles | 6 | 4 original + 2 cross-platform | Ready to publish |
| Growth Tracking | 2 | — | Templates ready |
| Email Marketing | 1 | 5-email sequence | Ready (needs infra) |
| Competitive Analysis | 1 | — | Done |
| ProductHunt Kit | 4 | Launch kit + coordination + blocker tracker + readiness audit | Ready |
| SEO Strategy + Articles | 5 | Strategy + 4 articles | Ready (needs /blog) |
| KOL Outreach | 3 | Strategy + target list + email sequences | Ready (needs Twitter) |
| Developer Advocate Kit | 1 | Awesome-list PRs + directory submissions + cross-post plan | Ready (needs /blog for canonical URLs) |
| **Total files** | **36** | | |

**Marketing content readiness: 99%.** Only remaining work is real-time post-launch iteration content.

**Bottleneck is 100% on non-marketing teams.** All P0 blockers require Board or Engineering action.

### Critical Escalation Note

The CMO has now produced 36 marketing files totaling 80 tweets, 9 blog/SEO articles (4 original + 2 cross-platform + 3 SEO), GTM strategy, PH launch kit, email sequences, KOL outreach plans + email sequences, competitive analysis, and developer advocate materials. **Zero pieces of this content can be deployed** because:

1. **Board has not created Twitter/Discord accounts** (flagged 8+ times)
2. **Engineering has not built /blog route** (flagged 5+ times)
3. **No gallery images or demo video exist** (PH launch requirement)

**Recommendation to CEO:** Schedule a 30-minute "unblock marketing" session with Board. Two actions (Twitter registration + Discord creation) would immediately unlock 80% of the prepared content pipeline.
