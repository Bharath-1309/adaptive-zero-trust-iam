# Adaptive Zero Trust Identity and Access Management

## Project Overview

Adaptive Zero Trust Identity and Access Management with Geolocation-Based Risk Assessment.

This is a final-year B.Tech Cybersecurity Engineering project focused on implementing a centralized and adaptive Identity and Access Management (IAM) system based on Zero Trust security principles.

The system evaluates user identity, permissions, device information, geolocation, authentication context and contextual risk before granting access to protected resources.

## Approved Project Objectives

1. To Design a centralized and secure Identity and Access Management (IAM) architecture based on Zero Trust principles.

2. To Develop a user authentication and Role-Based Access Control (RBAC) system for managing user identities and permissions.

3. To Implement adaptive access control to improve security through context-aware access evaluation and permission verification.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS |
| Backend | Python 3.13, FastAPI |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation | Pydantic |
| Identity Provider | Keycloak |
| Authentication | OpenID Connect / OAuth 2.0 |
| Token Format | JWT |
| Database | PostgreSQL |
| Geolocation | MaxMind GeoLite2 |
| Optional GPS | Browser Geolocation API |
| Maps | Leaflet, OpenStreetMap |
| Authorization | RBAC + ABAC |
| Risk Engine | Python-based explainable rule engine |
| Deployment | Docker Compose |

## Core Modules

1. Centralized Identity Management
2. Keycloak Authentication
3. JWT Validation
4. Role-Based Access Control
5. Attribute-Based Access Control
6. Device Recognition
7. IP-Based Geolocation
8. Optional Browser GPS
9. Explainable Risk Assessment
10. Login-Level Adaptive Evaluation
11. Sensitive-Action Risk Evaluation
12. Step-Up Multi-Factor Authentication
13. Security Audit Logging
14. Security Monitoring and Dashboard
15. Privileged Access Management

## Database Architecture

The application database contains exactly 15 tables:

### Identity and RBAC
- users
- roles
- permissions
- user_roles
- role_permissions

### Device and Authentication
- devices
- login_events
- location_observations

### Risk and Authorization
- risk_assessments
- access_decisions
- access_policies

### Security and Authentication Challenges
- audit_logs
- step_up_challenges

### Privileged Access Management
- privileged_access_requests
- privileged_access_grants

Keycloak uses a separate PostgreSQL database.

## Security Principles

- Never trust by default.
- Verify identity before granting access.
- Enforce backend authorization.
- Require RBAC permission verification.
- Evaluate ABAC policies.
- Assess contextual security risk.
- Require step-up MFA when applicable.
- Reauthorize sensitive operations.
- Maintain security audit history.
- Apply least privilege.

## Implementation Roadmap

1. Database schema and relationships
2. Project directory and development environment
3. Docker Compose and PostgreSQL
4. Keycloak configuration
5. FastAPI and JWT integration
6. RBAC implementation
7. ABAC implementation
8. IP geolocation
9. Optional browser GPS
10. Device recognition
11. Risk engine
12. Login-level risk evaluation
13. Sensitive-action risk evaluation
14. Step-up MFA
15. Audit logging and monitoring
16. React frontend
17. Frontend and backend integration
18. Functional and security testing
19. Privileged Access Management
20. Documentation and demonstration

## Development Status

Current phase: Phase 2 - Project Directory and Development Environment.

Database specification: Finalized.

Implementation: In progress.

## Repository

GitHub: https://github.com/Bharath-1309

## Developer

Bharath_D_S

B.Tech - Cybersecurity Engineering

