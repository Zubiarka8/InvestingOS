# The Closer skill

Eleven Claude skills that run your whole sales team. Free, MIT, no signup, no API key, no CRM seats.

`record-keeper` `prospector` `follow-up` `sales-coach` `contract-writer` `researcher`
`scheduler` `pipeline` `proposal-writer` `win-back` `forecaster`

One logs every email and call for you. Another finds new leads and does the cold outreach. One keeps
following up until a call is booked. And the craziest one is the coach: it listens to your sales call
and tells you exactly what to say next. When they say "it's too expensive", the perfect answer is
already on your screen. Then it writes the contract and sends it over.

So instead of paying for a CRM, a lead tool, an email sequencer and a call coach, you run the whole
thing inside Claude, from one file in your project.

Nothing is ever sent, booked or signed without your yes. Claude drafts, you approve, it goes out from
your own accounts.

## Install

Paste this repo link into Claude and say `install skill`:

```
https://github.com/Jakeschincariol/closer-skill

install skill
```

Or as a plugin, in Claude Code:

```
/plugin marketplace add Jakeschincariol/closer-skill
/plugin install closer-skill@closer-skill
```

Claude Code namespaces plugin skills, so installed as a plugin they show up as
`/closer-skill:prospector` and so on. Copy the folders instead if you want plain
`/prospector`:

```bash
git clone https://github.com/Jakeschincariol/closer-skill.git
cd closer-skill && cp -r record-keeper prospector follow-up sales-coach contract-writer researcher \
    scheduler pipeline proposal-writer win-back forecaster ~/.claude/skills/
```

Keep all eleven together: they share `pipeline/deals.py`. No Claude Code at all? Paste any single
`SKILL.md` at the top of a chat and it runs as a mode. You lose the Python tools, but the method works.
The tools need Python 3.8 or newer. Nothing to pip install.

Works best with Claude's Gmail and Google Calendar connectors (email and invites go out from your own
accounts) and Claude in Chrome (the coach reads Google Meet's live captions).

## The eleven

| skill | job | what it does |
| --- | --- | --- |
| `record-keeper` | Record Keeper | Logs every email and call for you: syncs your inbox threads with each contact, saves call notes, shows anyone's full history. |
| `prospector` | Prospector | Finds local businesses from public listings, checks each website for the gap you fix (no booking, not mobile, slow, no ads, no reviews) and writes the cold email. |
| `follow-up` | Follow-Up | Follows up until a call is booked: a bump, something useful, a last note. Stops at the first no. |
| `sales-coach` | Sales Coach | Listens to your call through live captions and tells you what to say next when an objection lands. Reviews the call after. |
| `contract-writer` | Contract Writer | Turns what was agreed into a plain-English services agreement and PDF, checks the fee against the call, and sends it on your yes. |
| `researcher` | Researcher | Reads the prospect's own website before the call and writes a one-page brief with talking points and questions. |
| `scheduler` | Scheduler | Turns "Thursday at 2 works" into a calendar invite with a Meet link, with no double-booking. |
| `pipeline` | Pipeline Manager | One board for every deal, from lead to won: the CRM, in `closer/pipeline.json`. |
| `proposal-writer` | Proposal Writer | Turns the call into a priced proposal with two or three clear options, in their own words. |
| `win-back` | Win-Back | Brings back the deals that went quiet, once, at the right time. |
| `forecaster` | Forecaster | Tells you what you'll close this month: commit, likely and best case, deal by deal. |

## How to use it

Everything lands in a `closer/` folder in your project, and each skill reads what the last one wrote.

An example, the one in the reel: a small web agency in Austin selling booking-ready websites.

1. **`pipeline`** sets up the board with your offer: $2,500, or a $399 monthly plan, and one true line
   about what it pays back.
2. **`prospector`** finds 47 local businesses with no online booking, ranks them with the reason, and
   writes the first email to Dana Ortiz at Harbor Lane Dental. You say yes. It goes out Monday 9:02 AM.
3. **`follow-up`** sends a bump on Wednesday, a 1-minute mockup on Friday and a last note on Tuesday,
   each on your yes. Dana replies at 11:48 AM: "Sorry, crazy week! Thursday at 2 works."
4. **`scheduler`** books Thursday, October 29, 2:00 PM on your calendar with a Meet link.
5. **`researcher`** writes the brief on Harbor Lane Dental before the call.
6. **`sales-coach`** reads the captions. Dana says, "It looks great, but honestly, it's too expensive
   for us right now." On your screen: "Totally fair. Most practices win the cost back with 2 new patients
   a month. Want to start on the $399 monthly plan instead, with no setup fee?"
7. **`contract-writer`** has the agreement for $399 a month out at 2:31 PM, on your yes.
8. **`record-keeper`** logged every email and the call. **`forecaster`** puts it in November's commit.
   **`proposal-writer`** and **`win-back`** handle the deals that need a quote or went quiet.

(The agency, Dana, Harbor Lane Dental and every lead are fictional.)

## The tools

All standard-library Python. The two that read websites read public pages only, identify themselves,
and go slowly.

```bash
python3 pipeline/deals.py board                                   # the board
python3 record-keeper/log.py sync --emails closer/inbox.json      # log every email
python3 prospector/leads.py rank --csv closer/leads.csv           # ranked leads -> closer/leads.json
python3 follow-up/followup.py due                                 # who to follow up with today
python3 sales-coach/coach.py listen --captions closer/calls/live.txt --follow
python3 contract-writer/contract.py draft --help
python3 researcher/brief.py build --contact <id>
python3 scheduler/slots.py parse --text "Thursday at 2 works"
python3 proposal-writer/proposal.py draft --help
python3 win-back/winback.py list
python3 forecaster/forecast.py month
```

Try any of them on the reel's example board with `--file pipeline/pipeline.example.json`.
The tests live next to each tool:

```bash
for d in */; do python3 -m unittest discover -s "$d" -p "test_*.py"; done
```

## Fine print

**Nothing goes out without your yes.** Every email, follow-up, invite, proposal and contract is a draft
until you approve that exact one. One yes per message, never "yes to all". Email goes out from your own
inbox, invites from your own calendar.

**Cold email, done legally.** Every opening email has a real subject, your real name and business, your
postal address and a plain way to opt out (CAN-SPAM). In the UK, EU and Canada, cold email to people needs
a lawful basis or consent first: check before you email there. At most 50 new openings a day.

**Stop rules.** At the first "no" it stops, everywhere, for good. Follow-ups stop the moment a call is
booked, after 3 follow-ups, or 30 days after the opening. Win-backs are one per deal. An unsubscribe goes
on a suppression list no skill will email.

**Calls.** Tell everyone on the call that captions or notes are on. Some places (California, Florida,
Washington and many countries) need everyone's consent to record. The coach reads captions as text, keeps
no audio, and shows its cards only to you. It never speaks on the call.

**Never invents anything.** No made-up facts about a prospect, numbers, results, clients, reviews or
deadlines. Answers and proposals are filled from your own offer and what was really said.

**Public business information only.** The researcher and prospector read a business's own website and
public listings, never a person's private life and nothing behind a login.

**Not legal or financial advice.** Contracts and proposals are templates: have a lawyer read your
standard terms once. Forecasts are estimates.

## Files

```
pipeline/          SKILL.md, deals.py, pipeline.example.json
record-keeper/     SKILL.md, log.py
prospector/        SKILL.md, leads.py, openers.json, leads.example.csv
follow-up/         SKILL.md, followup.py, templates.json
sales-coach/       SKILL.md, coach.py, objections.json, call.example.txt
contract-writer/   SKILL.md, contract.py
researcher/        SKILL.md, brief.py
scheduler/         SKILL.md, slots.py
proposal-writer/   SKILL.md, proposal.py, options.example.json
win-back/          SKILL.md, winback.py
forecaster/        SKILL.md, forecast.py
*/test_*.py        unittest suite, offline
```

MIT. Made by [Jake Schincariol](https://opusjake.ai).
