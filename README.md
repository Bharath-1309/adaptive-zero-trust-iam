# Adaptive Zero Trust Identity and Access Management

### With Geolocation-Based Risk Assessment

An adaptive cybersecurity system implementing Zero Trust security principles through identity verification, role-based and attribute-based access control, device trust, geolocation awareness, and contextual risk assessment.

---

## 1. Overview

Traditional access control systems often rely on predefined permissions and assume that authenticated users can be trusted.

This project explores an adaptive Zero Trust approach in which access requests are evaluated using multiple contextual factors rather than relying solely on successful authentication.

The system is designed around the principle:

**Never Trust, Always Verify.**

Every access request should be evaluated based on identity, permissions, device information, location context, and associated risk.

## 2. Project Objectives

- Implement identity-centric access control.
- Integrate centralized authentication.
- Enforce Role-Based Access Control (RBAC).
- Implement Attribute-Based Access Control (ABAC).
- Evaluate device trust before granting access.
- Incorporate geolocation-based access assessment.
- Identify suspicious or unusual access patterns.
- Maintain audit records of access-related activities.
- Support adaptive authorization decisions based on contextual risk.

## 3. Key Features

The project is being developed with the following capabilities:

- **Centralized Authentication:** Keycloak integration for identity management and authentication.
- **Role-Based Access Control (RBAC):** Restricts access according to assigned user roles and permissions.
- **Attribute-Based Access Control (ABAC):** Evaluates contextual attributes when making authorization decisions.
- **Device Trust:** Incorporates device information into access evaluation.
- **Geolocation Assessment:** Uses location-related information to support contextual access decisions.
- **Geofencing:** Supports office-location boundaries and geofence-based evaluation.
- **Risk Assessment:** Evaluates contextual factors associated with access requests.
- **Travel Authorization:** Supports temporary travel-related authorization.
- **VPN Session Management:** Provides functionality for tracking VPN-related sessions.
- **Audit Logging:** Records relevant security and access activities.
- **Resource-Based Authorization:** Supports access policies associated with protected resources.

These capabilities are under active development and integration.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React, TypeScript |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Identity Provider | Keycloak |
| Authentication | JWT |
| Frontend Styling | CSS |
| Version Control | Git and GitHub |

## 5. System Architecture

The application follows a frontend-backend architecture.

```text
             User
               |
               v
       React Frontend
               |
               v
        FastAPI Backend
               |
       +-------+--------+
       |                |
       v                v
  Keycloak         Authorization
 Authentication       Engine
                          |
              +-----------+-----------+
              |           |           |
              v           v           v
            RBAC         ABAC      Device Trust
              |           |           |
              +-----------+-----------+
                          |
                          v
                 Risk Assessment
                          |
                          v
                Access Decision
                          |
                 +--------+--------+
                 |                 |
                 v                 v
              Allow              Deny
                 |
                 v
             PostgreSQL
                 |
                 v
             Audit Logs
```

*Conceptual architecture; implementation and integration are ongoing.*

## 6. Zero Trust Approach

The system explores contextual access evaluation using multiple security factors:

1. Identity verification.
2. User role and permissions.
3. User and resource attributes.
4. Device trust information.
5. Geolocation context.
6. Risk assessment.
7. Authorization decision.

The objective is to make access decisions based on the security context of each request.

## 7. Project Structure

```text
adaptive-zero-trust-iam/
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   ├── core/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── security/
│   │   └── services/
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── App.tsx
│       ├── index.css
│       └── main.tsx
│
├── .gitignore
└── README.md
```

## 8. Development Status

**Project Status: Active Development**

The project is being developed incrementally.

Current development areas include:

- Backend API development.
- Database models and migrations.
- Authentication and authorization.
- RBAC and ABAC implementation.
- Device trust evaluation.
- Geolocation and geofencing.
- Contextual risk assessment.
- Audit logging.
- Frontend integration.

Further integration, testing, security validation, and improvements are ongoing.

## 9. Future Enhancements

Potential future improvements include:

- Advanced adaptive risk scoring.
- Real-time security monitoring.
- Improved suspicious-location detection.
- Enhanced device posture verification.
- Automated security alerts.
- Comprehensive security testing.
- Detailed administrative monitoring dashboard.
- Improved explainability of access decisions.

## 10. Security

This project is intended for educational and research purposes.

- Never commit environment variables or credentials.
- Store sensitive configuration outside source code.
- Use appropriate authentication and authorization controls.
- Validate access decisions before deployment.
- Do not use the application in production without appropriate security testing.

## 11. Author

**Bharath D S**

B.Tech – Cyber Security Engineering

GM University

GitHub: [@Bharath-1309](https://github.com/Bharath-1309)

## 12. License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.