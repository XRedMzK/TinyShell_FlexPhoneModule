type StoredDeviceIdentity = {
  nickname: string | null;
  createdAt: string;
  algorithm: "ECDSA_P256";
  publicKeySpkiBase64: string;
  deviceId: string;
  privateKey: CryptoKey;
  publicKey: CryptoKey;
};

const DB_NAME = "flexphone-db";
const STORE_NAME = "device";
const DEVICE_RECORD_KEY = "identity";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function getRecord<T>(db: IDBDatabase, key: IDBValidKey): Promise<T | undefined> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const request = store.get(key);

    request.onsuccess = () => resolve(request.result as T | undefined);
    request.onerror = () => reject(request.error);
  });
}

function putRecord<T>(db: IDBDatabase, key: IDBValidKey, value: T): Promise<void> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const request = store.put(value, key);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

function arrayBufferToBase64Url(buffer: ArrayBuffer): string {
  return arrayBufferToBase64(buffer).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function bytesToHex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function sha256Hex(data: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", data);
  return bytesToHex(digest);
}

export type DeviceIdentity = {
  nickname: string | null;
  createdAt: string;
  algorithm: "ECDSA_P256";
  publicKeySpkiBase64: string;
  deviceId: string;
};

export async function getDeviceIdentity(): Promise<DeviceIdentity | null> {
  const db = await openDb();
  const record = await getRecord<StoredDeviceIdentity>(db, DEVICE_RECORD_KEY);

  if (!record) return null;

  return {
    nickname: record.nickname,
    createdAt: record.createdAt,
    algorithm: record.algorithm,
    publicKeySpkiBase64: record.publicKeySpkiBase64,
    deviceId: record.deviceId,
  };
}

export async function getOrCreateDeviceIdentity(): Promise<DeviceIdentity> {
  const existing = await getDeviceIdentity();
  if (existing) return existing;

  const keyPair = await crypto.subtle.generateKey(
    {
      name: "ECDSA",
      namedCurve: "P-256",
    },
    false,
    ["sign", "verify"],
  );

  const publicKeySpki = await crypto.subtle.exportKey("spki", keyPair.publicKey);
  const publicKeySpkiBase64 = arrayBufferToBase64(publicKeySpki);
  const deviceId = await sha256Hex(publicKeySpki);

  const record: StoredDeviceIdentity = {
    nickname: null,
    createdAt: new Date().toISOString(),
    algorithm: "ECDSA_P256",
    publicKeySpkiBase64,
    deviceId,
    privateKey: keyPair.privateKey,
    publicKey: keyPair.publicKey,
  };

  const db = await openDb();
  await putRecord(db, DEVICE_RECORD_KEY, record);

  return {
    nickname: record.nickname,
    createdAt: record.createdAt,
    algorithm: record.algorithm,
    publicKeySpkiBase64: record.publicKeySpkiBase64,
    deviceId: record.deviceId,
  };
}

export async function setDeviceNickname(nickname: string): Promise<void> {
  const db = await openDb();
  const record = await getRecord<StoredDeviceIdentity>(db, DEVICE_RECORD_KEY);

  if (!record) {
    throw new Error("Device identity is not initialized.");
  }

  record.nickname = nickname;
  await putRecord(db, DEVICE_RECORD_KEY, record);
}

export async function signAuthCanonicalPayload(canonicalPayload: string): Promise<string> {
  const db = await openDb();
  const record = await getRecord<StoredDeviceIdentity>(db, DEVICE_RECORD_KEY);
  if (!record) {
    throw new Error("Device identity is not initialized.");
  }

  const signature = await crypto.subtle.sign(
    {
      name: "ECDSA",
      hash: { name: "SHA-256" },
    },
    record.privateKey,
    new TextEncoder().encode(canonicalPayload),
  );
  return arrayBufferToBase64Url(signature);
}
