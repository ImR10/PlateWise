# UniDine MVP - Sequence Flow

Scope: MVP only. One campus (UGA), guest mode, local-browser preferences, deterministic
recommendations, and explicit freshness/allergen safety handling.

Actors:

- **Student** - browses a dining hall menu and requests meal recommendations.
- **Dining Hall Admin/Manager** - maintains authorized food info through the dashboard. In this
  MVP the admin dashboard is the authorized data source of record (no scraping), which sidesteps the
  third-party terms-of-use problem.

The recommendation engine is a deterministic module inside the FastAPI service; it is drawn as a
separate participant only for readability.

```mermaid
sequenceDiagram
    actor Admin as Dining Hall Admin/Manager
    actor Student
    participant Web as Web (Next.js)
    participant API as API (FastAPI)
    participant Rec as Recommendation Engine
    participant DB as PostgreSQL

    Note over Rec: Deterministic module inside the API service (shown separately for clarity)

    Note over Admin,DB: Phase A - Admin maintains authorized food info (data source of record)
    Admin->>Web: Open dining dashboard
    Web->>API: GET existing dining halls / stations / menu-services
    API->>DB: Query normalized menu domain
    DB-->>API: Current records
    API-->>Web: Dashboard data
    Web-->>Admin: Show current halls, meals, foods

    Admin->>Web: Create/update foods (servings, calories, protein, carbs, fat, allergens, dietary tags)
    Web->>API: POST menu data for hall + date + meal period
    API->>DB: Save raw snapshot (hash, retrieved_at, source_updated_at)
    API->>DB: Upsert normalized records (idempotent, no duplicates)
    DB-->>API: Commit ok
    API-->>Web: Saved, freshness updated
    Web-->>Admin: Confirmation + data-quality status

    Note over Student,DB: Phase B - Student browses today's menu (guest mode)
    Student->>Web: Open UniDine (select UGA)
    Web->>API: GET /campuses/uga/dining-halls
    API->>DB: Fetch halls
    DB-->>API: Halls
    API-->>Web: Dining halls
    Student->>Web: Select dining hall + today's meal period
    Web->>API: GET /menu-services?campus=uga&date&hall&meal_period
    API->>DB: Fetch matching service
    DB-->>API: Service id
    Web->>API: GET /menu-services/{id}
    API->>DB: Fetch offerings, nutrition, allergens, provenance
    DB-->>API: Menu data + source_updated_at + freshness
    API-->>Web: Stations, foods, freshness_status, data_quality, warnings
    Web-->>Student: Show foods; mark missing nutrition as unknown (never zero) + stale/partial warnings

    Note over Student,Rec: Phase C - Student requests a recommendation
    Student->>Web: Enter calorie target, protein target, dietary prefs, allergen exclusions
    Web->>Web: Save targets/prefs to localStorage
    Student->>Web: Request plates
    Web->>API: POST /recommendations {menu_service_id, targets, excluded_allergens, required_tags}
    API->>DB: Load offerings for this service
    DB-->>API: Candidate offerings
    API->>Rec: Run deterministic constrained search
    Note over Rec: Hard constraints - respect allergen exclusions, exclude unknown-allergen items, enforce portion caps, require usable nutrition
    Rec-->>API: 2-3 plates + serving counts + totals + confidence + warning/explanation codes
    API-->>Web: Recommendation response (totals recompute from components)
    Web-->>Student: Show plate options with totals, confidence, freshness, safety messaging

    Note over Student,Rec: Phase D - Refine result
    alt Choose another returned option
        Student->>Web: Switch between the 2-3 plates
        Web-->>Student: Render alternate plate (client-side, no call)
    else Replace an unwanted item
        Student->>Web: Remove item and regenerate
        Web->>API: POST /recommendations {..., excluded_offering_ids}
        API->>Rec: Re-run with exclusions
        Rec-->>API: Updated plates
        API-->>Web: New recommendation
        Web-->>Student: Updated plate + safety messaging
    end
```

## Key MVP decisions encoded in the diagram

- **Admin dashboard = authorized data source.** The manager writes food info; UniDine stores a raw
  snapshot (with `retrieved_at` / `source_updated_at` / hash) then upserts normalized records
  idempotently - no scraping, no duplicates on re-save.
- **Guest mode, no auth, local-first prefs.** Student targets/preferences live in `localStorage`; no
  accounts.
- **Safety is explicit.** Missing nutrition shown as unknown, never zero; unknown-allergen items are
  excluded from recommendations (browsable, but never treated as safe); portion caps enforced;
  displayed totals recompute from selected servings.
- **Recommendation engine is deterministic and inside the API** (drawn separately only for
  readability), returning 2-3 plates with confidence, freshness, and warning/explanation codes.
- **Replace vs. re-pick** are distinct: switching among the returned 2-3 options is client-side;
  replacing an item re-calls `POST /recommendations` with `excluded_offering_ids`.
