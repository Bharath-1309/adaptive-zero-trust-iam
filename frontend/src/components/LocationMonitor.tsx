import { useEffect } from "react";
import { useAuth } from "../auth/useAuth";

const API_URL = "http://127.0.0.1:8000/api/v1/locations";
const CAPTURE_INTERVAL = 2 * 60 * 1000;
const MAX_GPS_ACCURACY = 200;

export default function LocationMonitor() {
  const { isAuthenticated, user, getAccessToken } = useAuth();

  useEffect(() => {
    if (!isAuthenticated || !user?.id) return;

    if (!navigator.geolocation) {
      console.warn("Browser geolocation is unavailable.");
      return;
    }

    const permissionKey = `zt-location-permission-${user.id}`;

    let cancelled = false;
    let capturing = false;

    const recordPermission = async (
      outcome: "GRANTED" | "DENIED" | "UNAVAILABLE",
      reason?: string,
    ) => {
      const token = await getAccessToken();

      const response = await fetch(`${API_URL}/permission-event`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ outcome, reason }),
      });

      if (!response.ok) {
        throw new Error("Unable to record location permission event.");
      }
    };

    const captureLocation = async (position: GeolocationPosition) => {
      if (cancelled) return;

      const { latitude, longitude, accuracy } = position.coords;

      // Reject inaccurate readings instead of saving them.
      if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude) ||
        !Number.isFinite(accuracy) ||
        accuracy <= 0 ||
        accuracy > MAX_GPS_ACCURACY
      ) {
        console.warn("GPS reading rejected: accuracy is insufficient.", {
          accuracy,
          maximumAllowed: MAX_GPS_ACCURACY,
        });
        return;
      }

      try {
        const token = await getAccessToken();

        if (cancelled) return;

        if (!sessionStorage.getItem(permissionKey)) {
          await recordPermission("GRANTED");
          sessionStorage.setItem(permissionKey, "true");
        }

        if (cancelled) return;

        const response = await fetch(`${API_URL}/browser-gps`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            latitude,
            longitude,
            accuracy_meters: accuracy,
            consent_granted: true,
          }),
        });

        if (!response.ok) {
          throw new Error("Unable to save location observation.");
        }

        console.info("Location observation recorded.", {
          accuracy,
          latitude,
          longitude,
        });
      } catch (error) {
        console.error("Location capture failed:", error);
      }
    };

    const handleLocationError = async (
      error: GeolocationPositionError,
    ) => {
      if (cancelled) return;

      console.error("GPS error:", error.message);

      if (!sessionStorage.getItem(permissionKey)) {
        try {
          if (error.code === 1) {
            await recordPermission("DENIED", "PERMISSION_DENIED");
          } else {
            await recordPermission(
              "UNAVAILABLE",
              error.code === 3 ? "TIMEOUT" : "POSITION_UNAVAILABLE",
            );
          }

          sessionStorage.setItem(permissionKey, "true");
        } catch (auditError) {
          console.error("Location audit failed:", auditError);
        }
      }
    };

    const requestLocation = () => {
      if (cancelled || capturing) return;

      capturing = true;

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            await captureLocation(position);
          } finally {
            capturing = false;
          }
        },
        async (error) => {
          try {
            await handleLocationError(error);
          } finally {
            capturing = false;
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 30000,
          maximumAge: 0,
        },
      );
    };

    requestLocation();

    const intervalId = window.setInterval(
      requestLocation,
      CAPTURE_INTERVAL,
    );

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [isAuthenticated, user?.id, getAccessToken]);

  return null;
}
