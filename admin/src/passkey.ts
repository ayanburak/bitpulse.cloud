/**
 * file: src/passkey.ts
 * importable: createPasskey, usePasskey
 *
 * description: Asks the browser to make a passkey or to answer a challenge with one.
 */

// NOTE: The options come from the server as JSON and these browser functions take exactly that
// form, so no encoding library is needed.

type Options = Parameters<typeof PublicKeyCredential.parseRequestOptionsFromJSON>[0];
type NewOptions = Parameters<typeof PublicKeyCredential.parseCreationOptionsFromJSON>[0];

export async function createPasskey(options: NewOptions): Promise<unknown> {
  const publicKey = PublicKeyCredential.parseCreationOptionsFromJSON(options);
  const credential = (await navigator.credentials.create({ publicKey })) as PublicKeyCredential;
  return credential.toJSON();
}

export async function usePasskey(options: Options): Promise<unknown> {
  const publicKey = PublicKeyCredential.parseRequestOptionsFromJSON(options);
  const credential = (await navigator.credentials.get({ publicKey })) as PublicKeyCredential;
  return credential.toJSON();
}
