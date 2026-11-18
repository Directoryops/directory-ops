# Lead routing: email templates

Read this file before writing any lead email.

**Rules:**
- Plain text, short, friendly, sounds like the owner.
- `{lead_details}` = one line per entry in `lead_fields` as "Label: value", in config order. Leave out any line whose value is empty, "Other", "Not sure", "N/A" or similar filler. Any template line with an empty value (no phone, no email) is left out.
- `{needed_by}` = " for <date>" when `needed_by_field` is set and filled, otherwise nothing. Dates read "November 23, 2026".
- **No em dashes and no hyphens anywhere in the copy:** ranges are "X to Y" ("$150 to $250"), never "150-250". `send_mail.py` warns on hyphen ranges.
- Always include the physical address and the stop line (required for business email).
- Fill `{...}` from the lead, the listing and the config. **Never invent the signer's name or the postal address.** If `owner_first_name` or `sender.physical_address` is missing, write `[NEEDED: your first name]` / `[NEEDED: your postal address]` in their place: drafts are allowed, a real send is refused until the owner answers.
- **Which template:** A only for the business's one free lead (pass `--free`). If the business already has a free email, sent or waiting as a draft, use B or B2 (no `--free`). `send_mail.py --free` refuses a second free lead.

**Template A: free lead** (send with `--free`)

`{who_line}`: the customer picked this business (the lead came from its page, `lead_origin_listing_column` = this listing) → "A customer chose you on {site_name} and {ask_phrase}". Rerouted to a nearby business → "Someone near you just {ask_phrase}".

Subject: New {request_type} request in {lead_city}{needed_by}

```
Hi {business_name} team,

I run {site_name}, a directory of {niche_plural}. {who_line}, and I want to send it to you for free.

Name: {lead_name}
Phone: {lead_phone}
Email: {lead_email}
Location: {lead_city}, {lead_state}
{lead_details}
Notes: {lead_message}

No catch. If it's a good fit, I can send you more requests in your area. After this one, each lead is ${price_per_lead}, and you only pay for the ones you want. Just reply "yes" and I'll keep them coming.

{owner_first_name}
{site_name}
{physical_address}

Reply "stop" and I won't email you again.
```

**Template B: paid lead, with an unlock link** (free lead already used and `offer.unlock_url_template` is set)

Subject: New {request_type} request in {lead_city}{needed_by}

```
Hi {business_name} team,

New request near you on {site_name}:

Location: {lead_city}, {lead_state}
{lead_details}

Unlock the customer's name, phone and email for ${price_per_lead}: {unlock_url}

{owner_first_name}
{site_name}
{physical_address}

Reply "stop" and I won't email you again.
```

**Template B2: paid lead, no unlock link** (`offer.unlock_url_template` is blank)

Subject: New {request_type} request in {lead_city}{needed_by}

```
Hi {business_name} team,

New request near you on {site_name}:

Location: {lead_city}, {lead_state}
{lead_details}

Want the customer's name, phone and email? Reply "yes" and I'll send them over with an invoice for ${price_per_lead}.

{owner_first_name}
{site_name}
{physical_address}

Reply "stop" and I won't email you again.
```

**Template C: the one follow up** (same thread, `--reply-to-id`)

```
Hi again,

Just making sure you saw the {request_type} request I sent yesterday in {lead_city}. The customer is waiting on quotes, so a quick call today gives you the best shot at winning it.

{owner_first_name}

Reply "stop" and I won't email you again.
```

**Template D: auto reply to interested businesses** (`--kind reply`)

```
Great to hear, thanks {first_name_or_team}!

Here's how it works: when a new request comes in near you, I'll email you the details. If it looks good, you unlock the customer's contact info for ${price_per_lead}. No contract, no monthly fee, and you only pay for leads you want.

Talk soon,
{owner_first_name}

Reply "stop" and I won't email you again.
```
