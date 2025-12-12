Implements public landing page at `/` and moves authenticated experience to `/app`. Logged-out users can view marketing content; authentication required for app access.

## Changes

**New public landing page (`/`)**
- Header with navigation links to Home, Login, Sign Up
- Hero section with value proposition and CTAs
- Feature sections: For Listeners, For Advertisers, How It Works
- Responsive design matching existing gradient brand styling

**Routing restructure**
- `/` ->  Public landing (was protected Home)
- `/app` ->  Protected app area (Home component)
- `/login`, `/signup` ->  Remain public
- Payment routes ->  Remain protected

**Redirect flow updates**
- Login/signup success ->  `/app` (was `/`)
- Logout -> `/` (was `/login`)
- Unauthenticated protected access ->  `/login` (unchanged)

## Implementation

```jsx
// App.jsx routing
<Routes>
  {/* Public routes */}
  <Route path="/" element={<LandingPage />} />
  <Route path="/login" element={<Login />} />
  <Route path="/signup" element={<Signup />} />
  
  {/* Protected routes */}
  <Route path="/app" element={<ProtectedRoute><Home /></ProtectedRoute>} />
  // ...
</Routes>
```

## Screenshots

**Public Landing Page**
![Landing page with hero, features, and how it works sections](https://github.com/user-attachments/assets/36d5d374-6d38-490c-8b64-944a8affbc8c)

**Login Page**
![Login form](https://github.com/user-attachments/assets/641c3bf4-3500-45e9-90ec-3a7da3af44c1)

**Signup Page**
![Signup form](https://github.com/user-attachments/assets/b6bd1f7d-fd1b-4ad9-b65c-e9107ec4c203)

<!-- START COPILOT ORIGINAL PROMPT -->



<details>

<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>Public Landing Home Page + Protected App Shell</issue_title>
> <issue_description>Assignee: 
> Labels: frontend, routing, ux, feature
> 
> Create a public home page that’s visible without login to explain what Wavvy is, and move the authenticated experience into a separate protected “app area” (e.g., /app or /dashboard). Logged-out users can browse the landing page, but must log in to actually use the product.
> 
> 
> </issue_description>
> 
> ## Comments on the Issue (you are @copilot in this section)
> 
> <comments>
> <comment_new><author>@paolacalle</author><body>
> ### Behavior / Routing
> 
> 1. Public Routes (No Login Required)
>   - Implement / as a public landing page with:
>     - Brief explanation of Wavvy for both listeners & advertisers
>     - Call-to-action buttons: Sign Up and Log In
>     - Optional sections:
>       - “For Listeners”
>       - “For Advertisers”
>       - “How it Works” (ML recommendations overview)
> 
> 2. Implement /login as the login page. lvtwoodpecker/wavvy-music-database#16 
> 
> 3. Implement /signup as the signup page. lvtwoodpecker/wavvy-music-database#16 
> 
> 4. (Optional) Add static public pages such as /about, /faq, /pricing, etc.</body></comment_new>
> <comment_new><author>@paolacalle</author><body>
> ### Protected Routes (Login Required)
> 
> 1. Define /app or /dashboard as the primary authenticated app area.
> 2. Protect advertiser-related routes, for example: /advertiser, /campaigns
> 3. Protect any other API/data-driven routes that should not be public.</body></comment_new>
> <comment_new><author>@paolacalle</author><body>
> ### Redirect Logic
> 
> 1. If an unauthenticated user attempts to access a protected route:
>   - Redirect them to /login.
> 
> 2. After a successful login:
>   - Redirect the user to /app (or to the last attempted protected route, if tracked).
> 
> 3. On logout:
>   - Clear auth state (token + user info).
>   - Redirect the user to / (the public landing page).
> </body></comment_new>
> <comment_new><author>@paolacalle</author><body>
> ### Frontend Tasks -- Build Landing Page (/)
> 
> 1. Create a header with logo + navigation links: Home, Login, Sign Up
> 2. Build a hero section with: 
>   - Short tagline (e.g., “Wavvy — Discover Music. Power Campaigns. Smarter.”)
>   - Two buttons: Sign Up and Log In 
> 3. Add basic informational sections:
>   - Listener Experience (how Wavvy helps listeners discover music).
>   - Advertiser Tools (campaigns, analytics, targeting).
>   - “How It Works” (high-level ML recommendation description).
> 4. Use placeholder imagery/components for now (can be improved later).</body></comment_new>
> </comments>
> 


</details>



<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes lvtwoodpecker/wavvy-music-database#19

[![Demo Video](path/to/thumbnail.png)](https://github.com/your-username/your-repo/raw/main/path/to/video.mp4)
