import { useEffect, useRef, useState } from "react";
import "./App.css";
import {
  getOrCreateDeviceIdentity,
  signAuthCanonicalPayload,
  setDeviceNickname,
  type DeviceIdentity,
} from "./lib/deviceIdentity";
import {
  createSignalingSocket,
  fetchIceConfiguration,
  registerDevice,
  requestAuthChallenge,
  verifyAuthChallenge,
} from "./lib/api";

type Screen = "login" | "home";

type SignalingMessageType =
  | "call.invite"
  | "call.ringing"
  | "call.accept"
  | "call.reject"
  | "call.cancel"
  | "call.hangup"
  | "call.error"
  | "webrtc.offer"
  | "webrtc.answer"
  | "webrtc.ice-candidate"
  | "webrtc.ice-restart"
  | "system.connected"
  | "system.ping"
  | "system.pong";

type OutgoingSignalingMessage = {
  type: Exclude<SignalingMessageType, "call.error" | "system.connected" | "system.pong">;
  call_id?: string;
  to_nickname?: string;
  target_device_id?: string;
  payload?: Record<string, unknown>;
};

type IncomingSignalingMessage = {
  type: SignalingMessageType;
  call_id?: string;
  from_nickname?: string;
  to_nickname?: string;
  from_device_id?: string;
  target_device_id?: string;
  timestamp?: string;
  payload?: unknown;
  error?: string;
};

type IncomingCall = {
  callId: string;
  fromNickname: string;
  fromDeviceId: string | null;
};

type CallSessionState =
  | "idle"
  | "outgoing_invite"
  | "incoming_invite"
  | "ringing"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "ended"
  | "failed";

type RuntimeFailureKind =
  | "none"
  | "signaling_failure"
  | "ice_degradation"
  | "media_failure";

type RuntimeFailureSource = Exclude<RuntimeFailureKind, "none">;

type RuntimeFailureContext = {
  kind: RuntimeFailureKind;
  code: string;
  userMessage: string;
  technicalDetails?: string;
  at: number;
};

const NO_RUNTIME_FAILURE: RuntimeFailureContext = {
  kind: "none",
  code: "none",
  userMessage: "No active failures",
  at: 0,
};

const ALLOWED_CALL_STATE_TRANSITIONS: Record<CallSessionState, CallSessionState[]> = {
  idle: ["outgoing_invite", "incoming_invite"],
  outgoing_invite: ["ringing", "connecting"],
  incoming_invite: ["connecting"],
  ringing: ["connecting"],
  connecting: ["connected", "reconnecting"],
  connected: ["reconnecting"],
  reconnecting: ["connected"],
  ended: ["idle", "outgoing_invite", "incoming_invite"],
  failed: ["idle", "outgoing_invite", "incoming_invite"],
};

function normalizeNickname(value: string) {
  const trimmed = value.trim().replace(/^@+/, "");
  return trimmed ? `@${trimmed}` : "";
}

function shortDeviceId(deviceId: string) {
  return `${deviceId.slice(0, 12)}...`;
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isRtcSessionDescriptionInit(value: unknown): value is RTCSessionDescriptionInit {
  if (!isObjectRecord(value) || typeof value.type !== "string") {
    return false;
  }

  return ["offer", "answer", "pranswer", "rollback"].includes(value.type);
}

function isRtcIceCandidateInit(value: unknown): value is RTCIceCandidateInit {
  return isObjectRecord(value) && typeof value.candidate === "string";
}

function isPolitePeer(localNickname: string, remoteNickname: string): boolean {
  return localNickname.localeCompare(remoteNickname) > 0;
}

function getIceCandidateType(candidate: string): string | null {
  const match = candidate.match(/\styp\s([a-zA-Z0-9]+)/);
  return match ? match[1].toLowerCase() : null;
}

function createCallId(): string {
  if ("randomUUID" in crypto && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatKbps(value: number | null): string {
  return value === null ? "n/a" : `${value.toFixed(1)} kbps`;
}

function formatMs(value: number | null): string {
  return value === null ? "n/a" : `${value.toFixed(1)} ms`;
}

function formatPackets(value: number | null): string {
  return value === null ? "n/a" : `${Math.max(0, Math.round(value))} packets`;
}

function formatRuntimeFailureKind(kind: RuntimeFailureKind): string {
  switch (kind) {
    case "signaling_failure":
      return "signaling failure";
    case "ice_degradation":
      return "ICE degradation";
    case "media_failure":
      return "media failure";
    default:
      return "none";
  }
}

function formatFailureTimestamp(at: number): string {
  if (!at) return "n/a";
  return new Date(at).toLocaleTimeString("ru-RU", { hour12: false });
}

function toErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function mapGetUserMediaError(errorName: string): { code: string; userMessage: string } {
  switch (errorName) {
    case "NotAllowedError":
      return {
        code: "microphone_permission_denied",
        userMessage: "Microphone access denied",
      };
    case "NotFoundError":
      return {
        code: "microphone_device_not_found",
        userMessage: "Microphone unavailable",
      };
    case "NotReadableError":
      return {
        code: "microphone_not_readable",
        userMessage: "Microphone is busy or unavailable",
      };
    default:
      return {
        code: "microphone_capture_failed",
        userMessage: "Media device error",
      };
  }
}

function mapGetDisplayMediaError(errorName: string): { code: string; userMessage: string } {
  switch (errorName) {
    case "NotAllowedError":
      return {
        code: "screen_permission_denied",
        userMessage: "Screen share access denied",
      };
    case "NotFoundError":
      return {
        code: "screen_source_not_found",
        userMessage: "Screen source unavailable",
      };
    case "NotReadableError":
      return {
        code: "screen_not_readable",
        userMessage: "Screen source is unavailable",
      };
    case "AbortError":
      return {
        code: "screen_selection_aborted",
        userMessage: "Screen share canceled",
      };
    case "InvalidStateError":
      return {
        code: "screen_invalid_state",
        userMessage: "Screen share failed",
      };
    default:
      return {
        code: "screen_capture_failed",
        userMessage: "Screen share failed",
      };
  }
}

function App() {
  const [screen, setScreen] = useState<Screen>("login");
  const [nicknameInput, setNicknameInput] = useState("");
  const [nickname, setNickname] = useState("");
  const [targetNicknameInput, setTargetNicknameInput] = useState("");
  const [deviceIdentity, setDeviceIdentity] = useState<DeviceIdentity | null>(null);
  const [identityStatus, setIdentityStatus] = useState("Initializing device identity...");
  const [identityReady, setIdentityReady] = useState(false);

  const [registerStatus, setRegisterStatus] = useState("Not registered");
  const [authStatus, setAuthStatus] = useState("Not authenticated");
  const [socketStatus, setSocketStatus] = useState("Disconnected");
  const [callStatus, setCallStatus] = useState("Idle");
  const [callSessionState, setCallSessionState] = useState<CallSessionState>("idle");
  const [incomingCall, setIncomingCall] = useState<IncomingCall | null>(null);
  const [screenShareStatus, setScreenShareStatus] = useState("Not sharing");
  const [remoteVideoStatus, setRemoteVideoStatus] = useState("No remote screen track.");
  const [iceConfigStatus, setIceConfigStatus] = useState("default STUN");
  const [iceCandidateStatus, setIceCandidateStatus] = useState("waiting");
  const [iceErrorStatus, setIceErrorStatus] = useState("none");
  const [heartbeatStatus, setHeartbeatStatus] = useState("stopped");
  const [statsStatus, setStatsStatus] = useState("idle");
  const [networkPathStatus, setNetworkPathStatus] = useState("unknown");
  const [audioBitrateStatus, setAudioBitrateStatus] = useState("n/a");
  const [screenBitrateStatus, setScreenBitrateStatus] = useState("n/a");
  const [screenResolutionStatus, setScreenResolutionStatus] = useState("n/a");
  const [remoteRttStatus, setRemoteRttStatus] = useState("n/a");
  const [remoteJitterStatus, setRemoteJitterStatus] = useState("n/a");
  const [remoteLossStatus, setRemoteLossStatus] = useState("n/a");
  const [runtimeFailure, setRuntimeFailure] = useState<RuntimeFailureContext>(NO_RUNTIME_FAILURE);
  const [lastSignalMessage, setLastSignalMessage] = useState("No signaling messages yet");

  const localNicknameRef = useRef("");
  const callSessionStateRef = useRef<CallSessionState>("idle");
  const socketRef = useRef<WebSocket | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);
  const screenVideoSenderRef = useRef<RTCRtpSender | null>(null);
  const remotePeerRef = useRef<string | null>(null);
  const activeCallIdRef = useRef<string | null>(null);
  const makingOfferRef = useRef(false);
  const ignoreOfferRef = useRef(false);
  const relayCandidateSeenRef = useRef(false);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null);
  const remoteMediaStreamRef = useRef<MediaStream>(new MediaStream());
  const iceServersRef = useRef<RTCIceServer[]>([{ urls: "stun:stun.l.google.com:19302" }]);
  const iceTransportPolicyRef = useRef<RTCIceTransportPolicy>("all");
  const statsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const inviteTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastHeartbeatPongMsRef = useRef(0);
  const iceRestartInProgressRef = useRef(false);
  const socketClosingIntentionallyRef = useRef(false);
  const authRefreshInProgressRef = useRef(false);
  const localAudioStopInProgressRef = useRef(false);
  const screenShareStopInProgressRef = useRef(false);
  const failureBySourceRef = useRef<Record<RuntimeFailureSource, RuntimeFailureContext | null>>({
    signaling_failure: null,
    ice_degradation: null,
    media_failure: null,
  });
  const previousStatsSampleRef = useRef<{
    timestampMs: number;
    outboundAudioBytes: number | null;
    outboundScreenBytes: number | null;
  } | null>(null);

  const publishRuntimeFailure = () => {
    const bySource = failureBySourceRef.current;
    const next =
      bySource.media_failure ?? bySource.signaling_failure ?? bySource.ice_degradation ?? NO_RUNTIME_FAILURE;
    setRuntimeFailure(next);
  };

  const setRuntimeFailureForSource = (
    source: RuntimeFailureSource,
    code: string,
    userMessage: string,
    technicalDetails?: string,
  ) => {
    failureBySourceRef.current[source] = {
      kind: source,
      code,
      userMessage,
      technicalDetails,
      at: Date.now(),
    };
    publishRuntimeFailure();
  };

  const clearRuntimeFailureSource = (source: RuntimeFailureSource) => {
    if (!failureBySourceRef.current[source]) return;
    failureBySourceRef.current[source] = null;
    publishRuntimeFailure();
  };

  const clearRuntimeFailureSourceCodes = (source: RuntimeFailureSource, codes: string[]) => {
    const current = failureBySourceRef.current[source];
    if (!current || !codes.includes(current.code)) return;
    failureBySourceRef.current[source] = null;
    publishRuntimeFailure();
  };

  const clearRuntimeFailures = (scope: "all" | "call" = "all") => {
    if (scope === "all") {
      failureBySourceRef.current.signaling_failure = null;
    }
    failureBySourceRef.current.ice_degradation = null;
    failureBySourceRef.current.media_failure = null;
    publishRuntimeFailure();
  };

  const setSessionState = (
    next: CallSessionState,
    options?: { force?: boolean; reasonCode?: string },
  ): boolean => {
    const current = callSessionStateRef.current;
    const isTerminalOrReset = next === "idle" || next === "ended" || next === "failed";
    const allowedFromCurrent =
      current === next || isTerminalOrReset || ALLOWED_CALL_STATE_TRANSITIONS[current].includes(next);

    if (!options?.force && !allowedFromCurrent) {
      const reasonSuffix = options?.reasonCode ? ` (${options.reasonCode})` : "";
      const errorMessage = `Invalid state transition ${current} -> ${next}${reasonSuffix}`;
      console.warn(errorMessage);
      setCallStatus(errorMessage);
      return false;
    }

    callSessionStateRef.current = next;
    setCallSessionState(next);
    return true;
  };

  const clearCallSession = () => {
    activeCallIdRef.current = null;
    setIncomingCall(null);
    setSessionState("idle");
  };

  const clearInviteTimeout = () => {
    if (inviteTimeoutRef.current) {
      clearTimeout(inviteTimeoutRef.current);
      inviteTimeoutRef.current = null;
    }
  };

  const startInviteTimeout = (callId: string, targetNickname: string) => {
    clearInviteTimeout();
    inviteTimeoutRef.current = setTimeout(() => {
      if (activeCallIdRef.current !== callId) return;
      if (callSessionStateRef.current !== "outgoing_invite" && callSessionStateRef.current !== "ringing") {
        return;
      }

      try {
        sendSignalingMessage({
          type: "call.cancel",
          call_id: callId,
          to_nickname: targetNickname,
          payload: { reason: "invite_timeout" },
        });
      } catch (error) {
        console.error(error);
      }

      setSessionState("ended");
      setCallStatus(`No answer from ${targetNickname} (timeout)`);
      closePeerConnection();
    }, 30_000);
  };

  const stopHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    setHeartbeatStatus("stopped");
  };

  const startHeartbeat = () => {
    if (heartbeatIntervalRef.current) return;
    lastHeartbeatPongMsRef.current = Date.now();
    setHeartbeatStatus("running");

    heartbeatIntervalRef.current = setInterval(() => {
      const socket = socketRef.current;
      if (!socket || socket.readyState !== WebSocket.OPEN) return;

      const nowMs = Date.now();
      if (nowMs - lastHeartbeatPongMsRef.current > 35_000) {
        setHeartbeatStatus("timeout");
        setRuntimeFailureForSource(
          "signaling_failure",
          "heartbeat_timeout",
          "Signaling reconnecting",
          "No pong received within timeout window",
        );
        socket.close();
        return;
      }

      try {
        sendSignalingMessage({
          type: "system.ping",
          payload: { ts: new Date().toISOString() },
        });
      } catch (error) {
        console.error(error);
      }
    }, 15_000);
  };

  const resetDiagnostics = () => {
    previousStatsSampleRef.current = null;
    if (statsIntervalRef.current) {
      clearInterval(statsIntervalRef.current);
      statsIntervalRef.current = null;
    }

    setStatsStatus("idle");
    setNetworkPathStatus("unknown");
    setAudioBitrateStatus("n/a");
    setScreenBitrateStatus("n/a");
    setScreenResolutionStatus("n/a");
    setRemoteRttStatus("n/a");
    setRemoteJitterStatus("n/a");
    setRemoteLossStatus("n/a");
    setIceErrorStatus("none");
    clearRuntimeFailureSource("ice_degradation");
  };

  const closePeerConnection = () => {
    peerConnectionRef.current?.close();
    peerConnectionRef.current = null;
    remotePeerRef.current = null;
    makingOfferRef.current = false;
    ignoreOfferRef.current = false;
    relayCandidateSeenRef.current = false;
    screenVideoSenderRef.current = null;

    const remoteStream = remoteMediaStreamRef.current;
    for (const track of remoteStream.getTracks()) {
      remoteStream.removeTrack(track);
    }

    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = null;
    }
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }

    setRemoteVideoStatus("No remote screen track.");
    setIceCandidateStatus("waiting");
    resetDiagnostics();
    clearInviteTimeout();
    iceRestartInProgressRef.current = false;
    clearRuntimeFailures("call");
    clearCallSession();
  };

  const stopLocalAudio = () => {
    localAudioStopInProgressRef.current = true;
    localStreamRef.current?.getTracks().forEach((track) => track.stop());
    localStreamRef.current = null;
    setTimeout(() => {
      localAudioStopInProgressRef.current = false;
    }, 0);
  };

  const stopScreenShare = async (reason: "user_stop" | "track_ended" = "user_stop") => {
    screenShareStopInProgressRef.current = true;
    const pc = peerConnectionRef.current;
    const screenSender = screenVideoSenderRef.current;

    if (pc && screenSender) {
      try {
        pc.removeTrack(screenSender);
      } catch (error) {
        console.error(error);
      }
    }

    screenVideoSenderRef.current = null;

    screenStreamRef.current?.getTracks().forEach((track) => track.stop());
    screenStreamRef.current = null;
    setScreenShareStatus("Not sharing");
    if (reason === "track_ended") {
      setRuntimeFailureForSource(
        "media_failure",
        "screen_track_ended",
        "Screen share stopped",
        "Display track ended",
      );
    } else {
      clearRuntimeFailureSourceCodes("media_failure", ["screen_track_ended", "screen_track_muted"]);
    }
    setTimeout(() => {
      screenShareStopInProgressRef.current = false;
    }, 0);
  };

  const sendSignalingMessage = (message: OutgoingSignalingMessage) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setRuntimeFailureForSource(
        "signaling_failure",
        "signaling_socket_unavailable",
        "Remote signaling unavailable",
        "Socket is not open",
      );
      throw new Error("Signaling socket is not connected.");
    }

    const fromNickname = localNicknameRef.current;
    if (!fromNickname) {
      throw new Error("Local nickname is not initialized.");
    }

    socket.send(
      JSON.stringify({
        ...message,
        from_nickname: fromNickname,
        from_device_id: deviceIdentity?.deviceId ?? null,
        timestamp: new Date().toISOString(),
      }),
    );

    if (failureBySourceRef.current.signaling_failure?.code === "signaling_socket_unavailable") {
      clearRuntimeFailureSource("signaling_failure");
    }
  };

  const ensureLocalAudioStream = async (): Promise<MediaStream> => {
    if (localStreamRef.current) return localStreamRef.current;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });

      for (const track of stream.getAudioTracks()) {
        track.onmute = () => {
          setRuntimeFailureForSource(
            "media_failure",
            "microphone_track_muted",
            "Microphone unavailable",
            "Local microphone track muted",
          );
        };
        track.onunmute = () => {
          clearRuntimeFailureSourceCodes("media_failure", ["microphone_track_muted"]);
        };
        track.onended = () => {
          if (localAudioStopInProgressRef.current) return;
          setRuntimeFailureForSource(
            "media_failure",
            "microphone_track_ended",
            "Microphone unavailable",
            "Local microphone track ended",
          );
        };
      }

      clearRuntimeFailureSourceCodes("media_failure", [
        "microphone_permission_denied",
        "microphone_device_not_found",
        "microphone_not_readable",
        "microphone_capture_failed",
        "microphone_track_muted",
        "microphone_track_ended",
      ]);
      localStreamRef.current = stream;
      return stream;
    } catch (error) {
      const errorName =
        error instanceof DOMException ? error.name : error instanceof Error ? error.name : "UnknownError";
      const mapped = mapGetUserMediaError(errorName);
      setRuntimeFailureForSource(
        "media_failure",
        mapped.code,
        mapped.userMessage,
        toErrorMessage(error, "getUserMedia failed"),
      );
      throw error;
    }
  };

  const tuneScreenSender = async (sender: RTCRtpSender) => {
    try {
      const parameters = sender.getParameters();
      if (!parameters.encodings || parameters.encodings.length === 0) {
        parameters.encodings = [{}];
      }

      parameters.encodings[0].maxBitrate = 2_500_000;
      await sender.setParameters(parameters);
    } catch (error) {
      console.error(error);
      setCallStatus("Failed to apply screen sender tuning");
    }
  };

  const pollPeerStats = async (pc: RTCPeerConnection) => {
    if (pc.connectionState === "closed") {
      resetDiagnostics();
      return;
    }

    try {
      const report = await pc.getStats();

      let selectedPairId: string | null = null;
      let selectedPairRttSeconds: number | null = null;
      let selectedLocalCandidateType: string | null = null;
      let selectedRemoteCandidateType: string | null = null;

      let outboundAudioBytes: number | null = null;
      let outboundScreenBytes: number | null = null;
      let outboundScreenWidth: number | null = null;
      let outboundScreenHeight: number | null = null;

      let remoteInboundAudioRttSeconds: number | null = null;
      let remoteInboundAudioLoss: number | null = null;
      let inboundAudioJitterSeconds: number | null = null;
      let inboundAudioLoss: number | null = null;

      report.forEach((stat) => {
        const record = stat as unknown as Record<string, unknown>;

        if (stat.type === "transport") {
          const pairId =
            typeof record.selectedCandidatePairId === "string"
              ? record.selectedCandidatePairId
              : null;
          if (pairId) {
            selectedPairId = pairId;
          }
          return;
        }

        if (stat.type === "candidate-pair") {
          if (selectedPairId) return;

          const pairState = typeof record.state === "string" ? record.state : "";
          const nominated = record.nominated === true;
          if (pairState === "succeeded" && nominated) {
            selectedPairId = stat.id;
          }
          return;
        }

        if (stat.type === "outbound-rtp") {
          if (record.isRemote === true) return;

          const mediaKind =
            typeof record.kind === "string"
              ? record.kind
              : typeof record.mediaType === "string"
                ? record.mediaType
                : "";

          if (mediaKind === "audio") {
            outboundAudioBytes =
              typeof record.bytesSent === "number" ? record.bytesSent : null;
            return;
          }

          if (mediaKind === "video") {
            outboundScreenBytes =
              typeof record.bytesSent === "number" ? record.bytesSent : null;

            if (typeof record.frameWidth === "number") {
              outboundScreenWidth = record.frameWidth;
            }
            if (typeof record.frameHeight === "number") {
              outboundScreenHeight = record.frameHeight;
            }
          }
          return;
        }

        if (stat.type === "remote-inbound-rtp") {
          const mediaKind =
            typeof record.kind === "string"
              ? record.kind
              : typeof record.mediaType === "string"
                ? record.mediaType
                : "";
          if (mediaKind === "audio") {
            if (typeof record.roundTripTime === "number") {
              remoteInboundAudioRttSeconds = record.roundTripTime;
            }
            if (typeof record.packetsLost === "number") {
              remoteInboundAudioLoss = record.packetsLost;
            }
          }
          return;
        }

        if (stat.type === "inbound-rtp") {
          const mediaKind =
            typeof record.kind === "string"
              ? record.kind
              : typeof record.mediaType === "string"
                ? record.mediaType
                : "";
          if (mediaKind === "audio") {
            if (typeof record.jitter === "number") {
              inboundAudioJitterSeconds = record.jitter;
            }
            if (typeof record.packetsLost === "number") {
              inboundAudioLoss = record.packetsLost;
            }
          }
        }
      });

      if (selectedPairId) {
        const pair = report.get(selectedPairId);
        const pairRecord = pair as (RTCStats & Record<string, unknown>) | undefined;
        if (pairRecord?.type === "candidate-pair") {
          const localCandidateId =
            typeof pairRecord.localCandidateId === "string" ? pairRecord.localCandidateId : null;
          const remoteCandidateId =
            typeof pairRecord.remoteCandidateId === "string" ? pairRecord.remoteCandidateId : null;

          if (typeof pairRecord.currentRoundTripTime === "number") {
            selectedPairRttSeconds = pairRecord.currentRoundTripTime;
          }

          if (localCandidateId) {
            const localCandidate = report.get(localCandidateId);
            const localRecord = localCandidate as (RTCStats & Record<string, unknown>) | undefined;
            if (localRecord && typeof localRecord.candidateType === "string") {
              selectedLocalCandidateType = localRecord.candidateType;
            }
          }

          if (remoteCandidateId) {
            const remoteCandidate = report.get(remoteCandidateId);
            const remoteRecord =
              remoteCandidate as (RTCStats & Record<string, unknown>) | undefined;
            if (remoteRecord && typeof remoteRecord.candidateType === "string") {
              selectedRemoteCandidateType = remoteRecord.candidateType;
            }
          }
        }
      }

      const nowMs = Date.now();
      const previous = previousStatsSampleRef.current;
      if (previous) {
        const elapsedMs = nowMs - previous.timestampMs;
        if (elapsedMs > 0) {
          let audioKbps: number | null = null;
          let screenKbps: number | null = null;

          if (previous.outboundAudioBytes !== null && outboundAudioBytes !== null) {
            const bytesDelta = Math.max(0, outboundAudioBytes - previous.outboundAudioBytes);
            audioKbps = (bytesDelta * 8) / (elapsedMs / 1000) / 1000;
          }

          if (previous.outboundScreenBytes !== null && outboundScreenBytes !== null) {
            const bytesDelta = Math.max(0, outboundScreenBytes - previous.outboundScreenBytes);
            screenKbps = (bytesDelta * 8) / (elapsedMs / 1000) / 1000;
          }

          setAudioBitrateStatus(formatKbps(audioKbps));
          setScreenBitrateStatus(formatKbps(screenKbps));
        }
      }

      previousStatsSampleRef.current = {
        timestampMs: nowMs,
        outboundAudioBytes,
        outboundScreenBytes,
      };

      if (outboundScreenWidth && outboundScreenHeight) {
        setScreenResolutionStatus(`${outboundScreenWidth}x${outboundScreenHeight}`);
      }

      const remoteRttMs =
        typeof remoteInboundAudioRttSeconds === "number"
          ? remoteInboundAudioRttSeconds * 1000
          : typeof selectedPairRttSeconds === "number"
            ? selectedPairRttSeconds * 1000
            : null;
      setRemoteRttStatus(formatMs(remoteRttMs));

      const remoteJitterMs =
        typeof inboundAudioJitterSeconds === "number" ? inboundAudioJitterSeconds * 1000 : null;
      setRemoteJitterStatus(formatMs(remoteJitterMs));

      const remoteLoss =
        typeof remoteInboundAudioLoss === "number"
          ? remoteInboundAudioLoss
          : typeof inboundAudioLoss === "number"
            ? inboundAudioLoss
            : null;
      setRemoteLossStatus(formatPackets(remoteLoss));

      const hasStatsDegradation =
        (remoteRttMs !== null && remoteRttMs > 1500) ||
        (remoteJitterMs !== null && remoteJitterMs > 200) ||
        (remoteLoss !== null && remoteLoss > 30);
      if (hasStatsDegradation) {
        setRuntimeFailureForSource(
          "ice_degradation",
          "stats_degraded",
          "Network unstable",
          `rtt=${formatMs(remoteRttMs)}, jitter=${formatMs(remoteJitterMs)}, loss=${formatPackets(remoteLoss)}`,
        );
      } else {
        clearRuntimeFailureSourceCodes("ice_degradation", ["stats_degraded"]);
      }

      const localType = selectedLocalCandidateType ?? "unknown";
      const remoteType = selectedRemoteCandidateType ?? "unknown";
      setNetworkPathStatus(`${localType} -> ${remoteType}`);

      if (localType === "relay" || remoteType === "relay") {
        setIceCandidateStatus("relay selected");
      }

      setStatsStatus("running");
    } catch (error) {
      console.error(error);
      setStatsStatus("failed");
    }
  };

  const startStatsPolling = (pc: RTCPeerConnection) => {
    if (statsIntervalRef.current) return;

    setStatsStatus("starting...");
    void pollPeerStats(pc);
    statsIntervalRef.current = setInterval(() => {
      void pollPeerStats(pc);
    }, 2000);
  };

  const requestIceRestart = async (
    pc: RTCPeerConnection,
    reason: string,
    notifyPeer: boolean,
  ) => {
    const target = remotePeerRef.current;
    const callId = activeCallIdRef.current;
    if (!target || !callId) return;
    if (pc.signalingState !== "stable") return;
    if (iceRestartInProgressRef.current) return;

    try {
      iceRestartInProgressRef.current = true;
      setSessionState("reconnecting");
      setCallStatus(`Reconnecting (${reason})...`);
      setRuntimeFailureForSource(
        "ice_degradation",
        "ice_restart_in_progress",
        "Reconnecting media path",
        `ICE restart reason=${reason}`,
      );

      if (notifyPeer) {
        sendSignalingMessage({
          type: "webrtc.ice-restart",
          call_id: callId,
          to_nickname: target,
          payload: { reason },
        });
      }

      makingOfferRef.current = true;
      const restartOffer = await pc.createOffer({ iceRestart: true });
      if (pc.signalingState !== "stable") return;

      await pc.setLocalDescription(restartOffer);
      if (!pc.localDescription) return;

      sendSignalingMessage({
        type: "webrtc.offer",
        call_id: callId,
        to_nickname: target,
        payload: {
          sdp: pc.localDescription.toJSON(),
          ice_restart: true,
        },
      });
    } catch (error) {
      console.error(error);
      setSessionState("failed");
      setCallStatus("ICE restart failed");
      setRuntimeFailureForSource(
        "ice_degradation",
        "ice_restart_failed",
        "Connection failed",
        toErrorMessage(error, "ICE restart failed"),
      );
    } finally {
      makingOfferRef.current = false;
      iceRestartInProgressRef.current = false;
    }
  };

  const negotiateConnection = async (pc: RTCPeerConnection) => {
    const target = remotePeerRef.current;
    const callId = activeCallIdRef.current;
    if (!target) return;
    if (!callId) return;
    if (pc.signalingState !== "stable") return;

    try {
      makingOfferRef.current = true;
      const offer = await pc.createOffer();
      if (pc.signalingState !== "stable") return;

      await pc.setLocalDescription(offer);
      if (!pc.localDescription) {
        throw new Error("Failed to create local offer.");
      }

      sendSignalingMessage({
        type: "webrtc.offer",
        call_id: callId,
        to_nickname: target,
        payload: {
          sdp: pc.localDescription.toJSON(),
        },
      });

      setCallStatus(`Negotiating with ${target}...`);
    } catch (error) {
      console.error(error);
      setCallStatus(error instanceof Error ? error.message : "Negotiation failed");
    } finally {
      makingOfferRef.current = false;
    }
  };

  const ensurePeerConnection = (remoteNickname: string): RTCPeerConnection => {
    const existing = peerConnectionRef.current;
    if (existing && remotePeerRef.current === remoteNickname) {
      startStatsPolling(existing);
      return existing;
    }

    if (existing) {
      closePeerConnection();
    }

    const pc = new RTCPeerConnection({
      iceServers: iceServersRef.current,
      iceTransportPolicy: iceTransportPolicyRef.current,
    });
    peerConnectionRef.current = pc;
    remotePeerRef.current = remoteNickname;

    pc.onicecandidate = (event) => {
      if (!event.candidate || !remotePeerRef.current) return;

      const candidateType = getIceCandidateType(event.candidate.candidate);
      if (candidateType) {
        if (candidateType === "relay") {
          relayCandidateSeenRef.current = true;
          setIceCandidateStatus("relay detected");
        } else if (!relayCandidateSeenRef.current) {
          setIceCandidateStatus(candidateType);
        }
      }

      try {
        sendSignalingMessage({
          type: "webrtc.ice-candidate",
          call_id: activeCallIdRef.current ?? undefined,
          to_nickname: remotePeerRef.current,
          payload: {
            candidate: event.candidate.toJSON(),
          },
        });
      } catch (error) {
        console.error(error);
      }
    };

    pc.onicecandidateerror = (event) => {
      const hostPart = event.address ? ` host=${event.address}` : "";
      const portPart = typeof event.port === "number" ? ` port=${event.port}` : "";
      const urlPart = event.url ? ` url=${event.url}` : "";
      const codePart = event.errorCode ? ` code=${event.errorCode}` : "";
      const textPart = event.errorText ? ` ${event.errorText}` : "";
      const details = `${codePart}${textPart}${hostPart}${portPart}${urlPart}`.trim() || "unknown";
      setIceErrorStatus(details);
      setRuntimeFailureForSource("ice_degradation", "ice_candidate_error", "Relay/ICE degraded", details);
    };

    pc.ontrack = (event) => {
      const track = event.track;
      const remoteStream = remoteMediaStreamRef.current;
      if (!remoteStream.getTracks().some((existingTrack) => existingTrack.id === track.id)) {
        remoteStream.addTrack(track);
      }

      if (remoteAudioRef.current) {
        remoteAudioRef.current.srcObject = remoteStream;
      }
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = remoteStream;
      }

      if (track.kind === "video") {
        setRemoteVideoStatus("Remote screen track active.");
        track.onended = () => {
          remoteStream.removeTrack(track);
          setRemoteVideoStatus("No remote screen track.");
          setRuntimeFailureForSource(
            "media_failure",
            "remote_video_track_ended",
            "Screen share stopped",
            "Remote video track ended",
          );
        };
        track.onmute = () => {
          setRuntimeFailureForSource(
            "media_failure",
            "remote_video_track_muted",
            "Screen share paused",
            "Remote video track muted",
          );
        };
        track.onunmute = () => {
          clearRuntimeFailureSourceCodes("media_failure", [
            "remote_video_track_muted",
            "remote_video_track_ended",
          ]);
        };
      }

      if (track.kind === "audio") {
        track.onended = () => {
          setRuntimeFailureForSource(
            "media_failure",
            "remote_audio_track_ended",
            "Remote audio stopped",
            "Remote audio track ended",
          );
        };
        track.onmute = () => {
          setRuntimeFailureForSource(
            "media_failure",
            "remote_audio_track_muted",
            "Remote audio muted",
            "Remote audio track muted",
          );
        };
        track.onunmute = () => {
          clearRuntimeFailureSourceCodes("media_failure", [
            "remote_audio_track_muted",
            "remote_audio_track_ended",
          ]);
        };
      }
    };

    pc.onnegotiationneeded = () => {
      void negotiateConnection(pc);
    };

    pc.onconnectionstatechange = () => {
      const remote = remotePeerRef.current ?? "peer";
      switch (pc.connectionState) {
        case "connected":
          setSessionState("connected");
          setCallStatus(`In call with ${remote}`);
          clearRuntimeFailureSource("ice_degradation");
          break;
        case "connecting":
          setSessionState("connecting");
          setCallStatus(`Connecting media with ${remote}...`);
          break;
        case "disconnected":
          setSessionState("reconnecting");
          setCallStatus("Peer disconnected");
          setRuntimeFailureForSource(
            "ice_degradation",
            "connection_disconnected",
            "Network unstable",
            "RTCPeerConnection connectionState=disconnected",
          );
          break;
        case "failed":
          setSessionState("failed");
          setCallStatus("Call failed");
          setRuntimeFailureForSource(
            "ice_degradation",
            "connection_failed",
            "Connection failed",
            "RTCPeerConnection connectionState=failed",
          );
          break;
        case "closed":
          setSessionState("ended");
          setCallStatus("Call closed");
          clearRuntimeFailures("call");
          break;
        default:
          break;
      }
    };

    pc.oniceconnectionstatechange = () => {
      if (pc.iceConnectionState === "failed") {
        setRuntimeFailureForSource(
          "ice_degradation",
          "ice_failed",
          "Connection failed",
          "iceConnectionState=failed",
        );
        void requestIceRestart(pc, "ice_failed", true);
        return;
      }

      if (pc.iceConnectionState === "disconnected") {
        setSessionState("reconnecting");
        setCallStatus("ICE disconnected, attempting recovery...");
        setRuntimeFailureForSource(
          "ice_degradation",
          "ice_disconnected",
          "Reconnecting media path",
          "iceConnectionState=disconnected",
        );
        return;
      }

      if (pc.iceConnectionState === "connected" || pc.iceConnectionState === "completed") {
        clearRuntimeFailureSource("ice_degradation");
        if (callSessionStateRef.current === "reconnecting") {
          setSessionState("connected");
          setCallStatus(`Recovered connection with ${remotePeerRef.current ?? "peer"}`);
        }
      }
    };

    startStatsPolling(pc);
    return pc;
  };

  const handleIncomingSignalingMessage = async (message: IncomingSignalingMessage) => {
    const messageType = message.type;
    const fromNickname = message.from_nickname;
    const callId = message.call_id ?? null;

    try {
      if (messageType === "call.error") {
        const reasonCode =
          isObjectRecord(message.payload) && typeof message.payload.reason_code === "string"
            ? message.payload.reason_code
            : null;
        const errorMessage = message.error ?? "Call signaling error";
        setCallStatus(reasonCode ? `${errorMessage} [${reasonCode}]` : errorMessage);
        setSessionState("failed", { reasonCode: reasonCode ?? undefined });
        clearInviteTimeout();
        return;
      }

      if (messageType === "system.connected") {
        return;
      }

      if (messageType === "system.pong") {
        lastHeartbeatPongMsRef.current = Date.now();
        setHeartbeatStatus("running");
        return;
      }

      if (!fromNickname || !fromNickname.startsWith("@")) {
        return;
      }

      if (messageType === "call.invite") {
        if (!callId) return;

        if (callSessionStateRef.current !== "idle" || activeCallIdRef.current) {
          sendSignalingMessage({
            type: "call.reject",
            call_id: callId,
            to_nickname: fromNickname,
            payload: { reason: "busy" },
          });
          return;
        }

        activeCallIdRef.current = callId;
        setIncomingCall({
          callId,
          fromNickname,
          fromDeviceId: message.from_device_id ?? null,
        });
        setSessionState("incoming_invite");
        setCallStatus(`Incoming call from ${fromNickname}`);
        setTargetNicknameInput(fromNickname);

        sendSignalingMessage({
          type: "call.ringing",
          call_id: callId,
          to_nickname: fromNickname,
        });
        return;
      }

      if (!callId || (activeCallIdRef.current && activeCallIdRef.current !== callId)) {
        return;
      }

      if (messageType === "call.ringing") {
        setSessionState("ringing");
        setCallStatus(`${fromNickname} is ringing...`);
        return;
      }

      if (messageType === "call.accept") {
        clearInviteTimeout();
        activeCallIdRef.current = callId;
        remotePeerRef.current = fromNickname;
        setSessionState("connecting");

        const localStream = await ensureLocalAudioStream();
        const pc = ensurePeerConnection(fromNickname);

        for (const track of localStream.getTracks()) {
          if (!pc.getSenders().some((sender) => sender.track?.id === track.id)) {
            pc.addTrack(track, localStream);
          }
        }

        setCallStatus(`Call accepted by ${fromNickname}. Negotiating...`);
        return;
      }

      if (messageType === "call.reject") {
        setCallStatus(`${fromNickname} rejected the call`);
        setSessionState("ended");
        clearInviteTimeout();
        stopLocalAudio();
        closePeerConnection();
        return;
      }

      if (messageType === "call.cancel") {
        setCallStatus(`Call canceled by ${fromNickname}`);
        setSessionState("ended");
        clearInviteTimeout();
        stopLocalAudio();
        closePeerConnection();
        return;
      }

      if (messageType === "call.hangup") {
        setCallStatus(`Call ended by ${fromNickname}`);
        setSessionState("ended");
        clearInviteTimeout();
        stopLocalAudio();
        closePeerConnection();
        return;
      }

      if (messageType === "webrtc.ice-restart") {
        const pc = peerConnectionRef.current;
        if (!pc) return;

        await requestIceRestart(pc, "remote_request", false);
        return;
      }

      if (messageType === "webrtc.offer") {
        if (!isObjectRecord(message.payload)) return;
        const sdp = message.payload.sdp;
        if (!isRtcSessionDescriptionInit(sdp)) return;

        activeCallIdRef.current = callId;
        setSessionState("connecting");

        const pc = ensurePeerConnection(fromNickname);
        const localStream = await ensureLocalAudioStream();
        for (const track of localStream.getTracks()) {
          if (!pc.getSenders().some((sender) => sender.track?.id === track.id)) {
            pc.addTrack(track, localStream);
          }
        }

        const collision = makingOfferRef.current || pc.signalingState !== "stable";
        const polite = isPolitePeer(localNicknameRef.current, fromNickname);
        ignoreOfferRef.current = !polite && collision;
        if (ignoreOfferRef.current) {
          setCallStatus(`Ignoring offer collision from ${fromNickname}`);
          return;
        }

        if (collision) {
          await Promise.all([
            pc.setLocalDescription({ type: "rollback" }),
            pc.setRemoteDescription(sdp),
          ]);
        } else {
          await pc.setRemoteDescription(sdp);
        }

        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        if (!pc.localDescription) {
          throw new Error("Failed to create local answer.");
        }

        sendSignalingMessage({
          type: "webrtc.answer",
          call_id: callId,
          to_nickname: fromNickname,
          payload: { sdp: pc.localDescription.toJSON() },
        });

        setIncomingCall(null);
        setCallStatus(`Answer sent to ${fromNickname}`);
        return;
      }

      if (messageType === "webrtc.answer") {
        if (!isObjectRecord(message.payload)) return;
        const sdp = message.payload.sdp;
        const pc = peerConnectionRef.current;
        if (!pc || !isRtcSessionDescriptionInit(sdp)) return;

        await pc.setRemoteDescription(sdp);
        setSessionState("connecting");
        setCallStatus(`Call established with ${fromNickname}`);
        return;
      }

      if (messageType === "webrtc.ice-candidate") {
        if (!isObjectRecord(message.payload)) return;
        const candidate = message.payload.candidate;
        const pc = peerConnectionRef.current;
        if (!pc || !isRtcIceCandidateInit(candidate)) return;
        if (ignoreOfferRef.current) return;

        await pc.addIceCandidate(candidate);
      }
    } catch (error) {
      console.error(error);
      setCallStatus(error instanceof Error ? error.message : "Failed to handle signaling message");
    }
  };

  useEffect(() => {
    callSessionStateRef.current = callSessionState;
  }, [callSessionState]);

  useEffect(() => {
    const init = async () => {
      try {
        const identity = await getOrCreateDeviceIdentity();
        setDeviceIdentity(identity);
        setIdentityStatus("Device identity is ready.");
        setIdentityReady(true);

        if (identity.nickname) {
          setNickname(identity.nickname);
          setNicknameInput(identity.nickname);
          localNicknameRef.current = identity.nickname;
        }
      } catch (error) {
        console.error(error);
        setIdentityStatus("Failed to initialize device identity.");
        setIdentityReady(false);
      }
    };

    void init();

    return () => {
      stopHeartbeat();
      clearInviteTimeout();
      socketClosingIntentionallyRef.current = true;
      socketRef.current?.close();
      closePeerConnection();
      stopLocalAudio();
      void stopScreenShare();
    };
  }, []);

  const loadIceConfiguration = async () => {
    try {
      const configuration = await fetchIceConfiguration();
      if (configuration.iceServers.length > 0) {
        iceServersRef.current = configuration.iceServers;
      } else {
        iceServersRef.current = [{ urls: "stun:stun.l.google.com:19302" }];
      }
      iceTransportPolicyRef.current = configuration.iceTransportPolicy;
      setIceConfigStatus(
        configuration.hasTurn
          ? `TURN configured (${configuration.iceTransportPolicy})`
          : "STUN only (TURN not configured)",
      );
    } catch (error) {
      console.error(error);
      iceServersRef.current = [{ urls: "stun:stun.l.google.com:19302" }];
      iceTransportPolicyRef.current = "all";
      setIceConfigStatus("failed to load, fallback to default STUN");
    }
  };

  const authenticateSignalingSession = async (
    normalizedNickname: string,
    identity: DeviceIdentity,
  ): Promise<string> => {
    setAuthStatus("Requesting challenge...");
    const challenge = await requestAuthChallenge({
      nickname: normalizedNickname,
      device_id: identity.deviceId,
    });

    setAuthStatus("Signing challenge...");
    const signature = await signAuthCanonicalPayload(challenge.canonical_payload);

    setAuthStatus("Verifying challenge...");
    const verified = await verifyAuthChallenge({
      challenge_id: challenge.challenge_id,
      nickname: normalizedNickname,
      device_id: identity.deviceId,
      signature,
    });

    const ttlSeconds = Math.max(0, verified.expires_at - Math.floor(Date.now() / 1000));
    setAuthStatus(`Authenticated (TTL ~${ttlSeconds}s)`);
    return verified.access_token;
  };

  const connectSignaling = (normalizedNickname: string, accessToken: string) => {
    const currentSocket = socketRef.current;
    if (
      currentSocket &&
      (currentSocket.readyState === WebSocket.OPEN || currentSocket.readyState === WebSocket.CONNECTING)
    ) {
      socketClosingIntentionallyRef.current = true;
      currentSocket.close();
    }

    setSocketStatus("Connecting...");
    const socket = createSignalingSocket(normalizedNickname, accessToken);
    socketRef.current = socket;

    socket.addEventListener("open", () => {
      setSocketStatus("Connected");
      lastHeartbeatPongMsRef.current = Date.now();
      startHeartbeat();
      clearRuntimeFailureSource("signaling_failure");
    });

    socket.addEventListener("message", (event) => {
      setLastSignalMessage(event.data);

      try {
        const message = JSON.parse(event.data) as IncomingSignalingMessage;
        if (!isObjectRecord(message)) return;
        if (typeof message.type !== "string") return;
        void handleIncomingSignalingMessage(message);
      } catch (error) {
        console.error(error);
      }
    });

    socket.addEventListener("close", (event) => {
      if (socketRef.current === socket) {
        socketRef.current = null;
      }

      setSocketStatus("Disconnected");
      stopHeartbeat();
      const isIntentional = socketClosingIntentionallyRef.current;
      socketClosingIntentionallyRef.current = false;

      if (!isIntentional && event.reason === "token_expired") {
        setAuthStatus("Token expired, refreshing...");
        void (async () => {
          if (authRefreshInProgressRef.current) return;

          const identity = deviceIdentity;
          const currentNickname = localNicknameRef.current;
          if (!identity || !currentNickname) {
            setAuthStatus("Re-auth failed");
            return;
          }

          authRefreshInProgressRef.current = true;
          try {
            const refreshedAccessToken = await authenticateSignalingSession(currentNickname, identity);
            connectSignaling(currentNickname, refreshedAccessToken);
          } catch (error) {
            console.error(error);
            setSocketStatus("Re-authentication failed");
            setAuthStatus("Re-auth failed");
            setRuntimeFailureForSource(
              "signaling_failure",
              "auth_refresh_failed",
              "Signaling auth failed",
              toErrorMessage(error, "Failed to refresh signaling token"),
            );
          } finally {
            authRefreshInProgressRef.current = false;
          }
        })();
        closePeerConnection();
        void stopScreenShare();
        return;
      }

      if (!isIntentional) {
        setRuntimeFailureForSource(
          "signaling_failure",
          "signaling_socket_closed",
          "Signaling lost",
          `code=${event.code} reason=${event.reason || "none"}`,
        );
      }
      closePeerConnection();
      void stopScreenShare();
    });

    socket.addEventListener("error", () => {
      setSocketStatus("Connection error");
      setHeartbeatStatus("error");
      setRuntimeFailureForSource(
        "signaling_failure",
        "signaling_socket_error",
        "Signaling reconnecting",
        "WebSocket error event",
      );
    });
  };

  const handleContinue = async () => {
    const normalized = normalizeNickname(nicknameInput);
    if (!normalized || !identityReady || !deviceIdentity) return;

    try {
      setRegisterStatus("Registering device...");
      setAuthStatus("Not authenticated");

      await setDeviceNickname(normalized);

      await registerDevice({
        nickname: normalized,
        device_id: deviceIdentity.deviceId,
        public_key_spki_base64: deviceIdentity.publicKeySpkiBase64,
      });
      await loadIceConfiguration();
      const accessToken = await authenticateSignalingSession(normalized, deviceIdentity);

      setNickname(normalized);
      localNicknameRef.current = normalized;
      setRegisterStatus("Registered");
      setScreen("home");
      clearRuntimeFailures("all");

      connectSignaling(normalized, accessToken);
    } catch (error) {
      console.error(error);
      setRegisterStatus(error instanceof Error ? error.message : "Registration failed");
      setAuthStatus(error instanceof Error ? error.message : "Authentication failed");
    }
  };

  const handleStartCall = async () => {
    const target = normalizeNickname(targetNicknameInput);
    const local = localNicknameRef.current;

    if (!target || !local) {
      setCallStatus("Enter target nickname.");
      return;
    }

    if (target === local) {
      setCallStatus("Target nickname must be different from your nickname.");
      return;
    }

    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      setCallStatus("Signaling socket is not connected.");
      return;
    }

    if (callSessionStateRef.current !== "idle") {
      setCallStatus("Another call session is already active.");
      return;
    }

    const callId = createCallId();
    activeCallIdRef.current = callId;
    remotePeerRef.current = target;
    setIncomingCall(null);
    setSessionState("outgoing_invite");
    setCallStatus(`Calling ${target}...`);
    startInviteTimeout(callId, target);
    try {
      sendSignalingMessage({
        type: "call.invite",
        call_id: callId,
        to_nickname: target,
        payload: { mode: "audio" },
      });
    } catch (error) {
      console.error(error);
      setCallStatus(error instanceof Error ? error.message : "Failed to send call invite");
      closePeerConnection();
    }
  };

  const handleShareScreen = async () => {
    if (screenVideoSenderRef.current) {
      await stopScreenShare("user_stop");
      return;
    }

    const pc = peerConnectionRef.current;
    if (!pc || !remotePeerRef.current) {
      setCallStatus("Start audio call before sharing screen.");
      return;
    }

    try {
      setScreenShareStatus("Selecting screen...");
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true,
      });

      const videoTrack = displayStream.getVideoTracks()[0];
      if (!videoTrack) {
        throw new Error("No display video track received.");
      }

      videoTrack.contentHint = "detail";

      const screenSender = pc.addTrack(videoTrack, displayStream);
      await tuneScreenSender(screenSender);
      screenVideoSenderRef.current = screenSender;
      screenStreamRef.current = displayStream;
      setScreenShareStatus("Sharing");
      setCallStatus(`Sharing screen with ${remotePeerRef.current}`);

      clearRuntimeFailureSourceCodes("media_failure", [
        "screen_permission_denied",
        "screen_source_not_found",
        "screen_not_readable",
        "screen_selection_aborted",
        "screen_invalid_state",
        "screen_capture_failed",
        "screen_track_ended",
        "screen_track_muted",
      ]);

      videoTrack.onmute = () => {
        setRuntimeFailureForSource(
          "media_failure",
          "screen_track_muted",
          "Screen share paused",
          "Display track muted",
        );
      };
      videoTrack.onunmute = () => {
        clearRuntimeFailureSourceCodes("media_failure", ["screen_track_muted"]);
      };
      videoTrack.onended = () => {
        if (screenShareStopInProgressRef.current) return;
        void stopScreenShare("track_ended");
      };
    } catch (error) {
      console.error(error);
      setScreenShareStatus("Not sharing");
      const errorName =
        error instanceof DOMException ? error.name : error instanceof Error ? error.name : "UnknownError";
      const mapped = mapGetDisplayMediaError(errorName);
      setRuntimeFailureForSource(
        "media_failure",
        mapped.code,
        mapped.userMessage,
        toErrorMessage(error, "getDisplayMedia failed"),
      );
      setCallStatus(toErrorMessage(error, "Screen share failed"));
    }
  };

  const handleAcceptIncomingCall = () => {
    if (!incomingCall) return;

    activeCallIdRef.current = incomingCall.callId;
    remotePeerRef.current = incomingCall.fromNickname;
    setIncomingCall(null);
    setSessionState("connecting");
    setCallStatus(`Accepted call from ${incomingCall.fromNickname}. Waiting for offer...`);

    try {
      sendSignalingMessage({
        type: "call.accept",
        call_id: activeCallIdRef.current ?? undefined,
        to_nickname: remotePeerRef.current ?? undefined,
        payload: { accepted: true },
      });
    } catch (error) {
      console.error(error);
      setCallStatus(error instanceof Error ? error.message : "Failed to accept incoming call");
      closePeerConnection();
    }
  };

  const handleRejectIncomingCall = () => {
    if (!incomingCall) return;
    const callId = incomingCall.callId;
    const from = incomingCall.fromNickname;

    try {
      sendSignalingMessage({
        type: "call.reject",
        call_id: callId,
        to_nickname: from,
        payload: { reason: "rejected" },
      });
    } catch (error) {
      console.error(error);
    }

    setCallStatus(`Rejected call from ${from}`);
    setIncomingCall(null);
    clearCallSession();
  };

  const handleEndCall = () => {
    const callId = activeCallIdRef.current;
    const peer = remotePeerRef.current;

    if (callId && peer) {
      try {
        if (callSessionStateRef.current === "outgoing_invite" || callSessionStateRef.current === "ringing") {
          sendSignalingMessage({
            type: "call.cancel",
            call_id: callId,
            to_nickname: peer,
            payload: { reason: "caller_canceled" },
          });
        } else if (
          callSessionStateRef.current === "connecting" ||
          callSessionStateRef.current === "connected" ||
          callSessionStateRef.current === "reconnecting"
        ) {
          sendSignalingMessage({
            type: "call.hangup",
            call_id: callId,
            to_nickname: peer,
            payload: { reason: "local_hangup" },
          });
        }
      } catch (error) {
        console.error(error);
      }
    }

    clearInviteTimeout();
    setSessionState("ended");
    setCallStatus("Call ended");
    stopLocalAudio();
    closePeerConnection();
    void stopScreenShare();
  };

  const handleLogout = () => {
    handleEndCall();
    stopHeartbeat();
    clearInviteTimeout();
    authRefreshInProgressRef.current = false;
    socketClosingIntentionallyRef.current = true;
    socketRef.current?.close();
    closePeerConnection();
    stopLocalAudio();
    void stopScreenShare();
    setScreen("login");
    setSocketStatus("Disconnected");
    setCallStatus("Idle");
    setScreenShareStatus("Not sharing");
    setAuthStatus("Not authenticated");
    setSessionState("idle");
    clearRuntimeFailures("all");
  };

  return (
    <main className="app-shell">
      <section className="card">
        <div className="brand">
          <h1>FlexPhone</h1>
          <p>Secure audio calls and screen sharing</p>
        </div>

        {screen === "login" ? (
          <div className="panel">
            <div className="identity-box">
              <div className="identity-title">Device identity</div>
              <div className="identity-status">{identityStatus}</div>

              {deviceIdentity && (
                <>
                  <div className="identity-line">
                    <span className="identity-label">Algorithm:</span>
                    <span>{deviceIdentity.algorithm}</span>
                  </div>
                  <div className="identity-line">
                    <span className="identity-label">Device ID:</span>
                    <span>{shortDeviceId(deviceIdentity.deviceId)}</span>
                  </div>
                </>
              )}
            </div>

            <label className="label" htmlFor="nickname">
              Nickname
            </label>

            <input
              id="nickname"
              className="input"
              type="text"
              placeholder="@user_name"
              value={nicknameInput}
              onChange={(e) => setNicknameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void handleContinue();
              }}
              disabled={!identityReady}
            />

            <button
              className="button primary"
              onClick={() => void handleContinue()}
              disabled={!identityReady}
            >
              Continue
            </button>

            <div className="identity-box compact">
              <div className="identity-line">
                <span className="identity-label">Register:</span>
                <span>{registerStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Auth:</span>
                <span>{authStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Signaling:</span>
                <span>{socketStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">ICE config:</span>
                <span>{iceConfigStatus}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="panel">
            <div className="welcome">
              <span className="status-dot" />
              <span>{nickname}</span>
            </div>

            <div className="identity-box compact">
              <div className="identity-line">
                <span className="identity-label">Device ID:</span>
                <span>{deviceIdentity ? shortDeviceId(deviceIdentity.deviceId) : "N/A"}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Register:</span>
                <span>{registerStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Auth:</span>
                <span>{authStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Signaling:</span>
                <span>{socketStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Call:</span>
                <span>{callStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Failure kind:</span>
                <span className={`failure-value ${runtimeFailure.kind}`}>
                  {formatRuntimeFailureKind(runtimeFailure.kind)}
                </span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Failure status:</span>
                <span>{runtimeFailure.userMessage}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Failure code:</span>
                <span>{runtimeFailure.code}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Failure at:</span>
                <span>{formatFailureTimestamp(runtimeFailure.at)}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Session:</span>
                <span>{callSessionState}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Screen:</span>
                <span>{screenShareStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">ICE config:</span>
                <span>{iceConfigStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">ICE candidates:</span>
                <span>{iceCandidateStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">ICE errors:</span>
                <span>{iceErrorStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Heartbeat:</span>
                <span>{heartbeatStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Stats:</span>
                <span>{statsStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Path:</span>
                <span>{networkPathStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Audio out:</span>
                <span>{audioBitrateStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Screen out:</span>
                <span>{screenBitrateStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Screen size:</span>
                <span>{screenResolutionStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">RTT:</span>
                <span>{remoteRttStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Jitter:</span>
                <span>{remoteJitterStatus}</span>
              </div>
              <div className="identity-line">
                <span className="identity-label">Loss:</span>
                <span>{remoteLossStatus}</span>
              </div>
              {runtimeFailure.technicalDetails ? (
                <div className="identity-line">
                  <span className="identity-label">Failure details:</span>
                  <span>{runtimeFailure.technicalDetails}</span>
                </div>
              ) : null}
            </div>

            <label className="label" htmlFor="target-nickname">
              Target nickname
            </label>
            <input
              id="target-nickname"
              className="input"
              type="text"
              placeholder="@peer_name"
              value={targetNicknameInput}
              onChange={(e) => setTargetNicknameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void handleStartCall();
              }}
            />

            {incomingCall ? (
              <>
                <div className="identity-box compact">
                  <div className="identity-title">Incoming call</div>
                  <div className="identity-status">
                    {incomingCall.fromNickname}
                    {incomingCall.fromDeviceId ? ` (${shortDeviceId(incomingCall.fromDeviceId)})` : ""}
                  </div>
                </div>
                <button className="button primary" onClick={handleAcceptIncomingCall}>
                  Accept Call
                </button>
                <button className="button secondary" onClick={handleRejectIncomingCall}>
                  Reject Call
                </button>
              </>
            ) : (
              <button className="button primary" onClick={() => void handleStartCall()}>
                Start Call
              </button>
            )}

            <button
              className="button secondary"
              onClick={() => handleEndCall()}
              disabled={callSessionState === "idle"}
            >
              {callSessionState === "outgoing_invite" || callSessionState === "ringing"
                ? "Cancel Call"
                : "Hang Up"}
            </button>
            <button
              className="button secondary"
              onClick={() => void handleShareScreen()}
              disabled={callSessionState !== "connected" && screenShareStatus !== "Sharing"}
            >
              {screenShareStatus === "Sharing" ? "Stop Sharing" : "Share Screen"}
            </button>
            <button className="button ghost" onClick={handleLogout}>
              Logout
            </button>

            <div className="identity-box compact">
              <div className="identity-title">Remote Screen</div>
              <video className="remote-video" ref={remoteVideoRef} autoPlay playsInline />
              <div className="identity-status">{remoteVideoStatus}</div>
            </div>

            <div className="identity-box compact">
              <div className="identity-title">Last signaling message</div>
              <div className="identity-status message-box">{lastSignalMessage}</div>
            </div>
          </div>
        )}
      </section>

      <audio ref={remoteAudioRef} autoPlay playsInline style={{ display: "none" }} />
    </main>
  );
}

export default App;
