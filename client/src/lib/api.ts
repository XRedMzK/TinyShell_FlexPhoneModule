const API_BASE_URL = "http://127.0.0.1:8000";
const WS_BASE_URL = "ws://127.0.0.1:8000";

export type RegisterDevicePayload = {
  nickname: string;
  device_id: string;
  public_key_spki_base64: string;
};

export type RegisterDeviceResponse = {
  ok: boolean;
  nickname: string;
  device_id: string;
};

export type AuthChallengePayload = {
  nickname: string;
  device_id: string;
};

export type AuthChallengeResponse = {
  challenge_id: string;
  nickname: string;
  device_id: string;
  nonce: string;
  issued_at: number;
  expires_at: number;
  algorithm: "ECDSA_P256_SHA256";
  payload_version: "flexphone-auth-v1";
  canonical_payload: string;
};

export type AuthVerifyPayload = {
  challenge_id: string;
  nickname: string;
  device_id: string;
  signature: string;
};

export type AuthVerifyResponse = {
  access_token: string;
  token_type: "Bearer";
  expires_at: number;
};

type IceServerApiRecord = {
  urls: string[];
  username?: string;
  credential?: string;
};

type IceServersApiResponse = {
  ice_servers: IceServerApiRecord[];
  ice_transport_policy: "all" | "relay";
  turn_credentials?: {
    mode: "static" | "ephemeral";
    username?: string;
    ttl_seconds?: number;
    expires_at_unix?: number;
    clock_skew_tolerance_seconds?: number;
    username_scheme?: string;
  };
};

export type IceConfiguration = {
  iceServers: RTCIceServer[];
  iceTransportPolicy: RTCIceTransportPolicy;
  hasTurn: boolean;
};

export async function registerDevice(
  payload: RegisterDevicePayload,
): Promise<RegisterDeviceResponse> {
  const response = await fetch(`${API_BASE_URL}/devices/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Device registration failed: ${response.status} ${text}`);
  }

  return response.json() as Promise<RegisterDeviceResponse>;
}

export function createSignalingSocket(nickname: string, accessToken: string): WebSocket {
  return new WebSocket(
    `${WS_BASE_URL}/ws/signaling/${encodeURIComponent(nickname)}?access_token=${encodeURIComponent(accessToken)}`,
  );
}

export async function requestAuthChallenge(
  payload: AuthChallengePayload,
): Promise<AuthChallengeResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/challenge`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Auth challenge failed: ${response.status} ${text}`);
  }

  return response.json() as Promise<AuthChallengeResponse>;
}

export async function verifyAuthChallenge(payload: AuthVerifyPayload): Promise<AuthVerifyResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Auth verify failed: ${response.status} ${text}`);
  }

  return response.json() as Promise<AuthVerifyResponse>;
}

export async function fetchIceConfiguration(): Promise<IceConfiguration> {
  const response = await fetch(`${API_BASE_URL}/webrtc/ice-servers`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to load ICE configuration: ${response.status} ${text}`);
  }

  const payload = (await response.json()) as IceServersApiResponse;
  const hasTurn = payload.ice_servers.some((server) =>
    server.urls.some((url) => url.startsWith("turn:") || url.startsWith("turns:")),
  );

  return {
    iceServers: payload.ice_servers.map((server) => ({
      urls: server.urls,
      username: server.username,
      credential: server.credential,
    })),
    iceTransportPolicy: payload.ice_transport_policy,
    hasTurn,
  };
}
