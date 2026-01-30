const inputs = new Map<string, string>();
const outputs = new Map<string, string>();
let failedMessage: string | null = null;
const infoMessages: string[] = [];
const warningMessages: string[] = [];
const errorMessages: string[] = [];

export function __setInputs(next: Record<string, string>) {
  inputs.clear();
  Object.entries(next).forEach(([key, value]) => inputs.set(key, value));
}

export function __reset() {
  inputs.clear();
  outputs.clear();
  failedMessage = null;
  infoMessages.length = 0;
  warningMessages.length = 0;
  errorMessages.length = 0;
}

export function __getState() {
  return {
    inputs: new Map(inputs),
    outputs: new Map(outputs),
    failedMessage,
    infoMessages: [...infoMessages],
    warningMessages: [...warningMessages],
    errorMessages: [...errorMessages]
  };
}

export function getInput(name: string, options: { required?: boolean } = {}) {
  const raw = inputs.get(name) ?? '';
  const value = String(raw);
  if (options.required && !value) {
    throw new Error(`Input required and not supplied: ${name}`);
  }
  return value;
}

export function setOutput(name: string, value: string) {
  outputs.set(name, value);
}

export function setFailed(message: string) {
  failedMessage = String(message);
}

export function info(message: string) {
  infoMessages.push(String(message));
}

export function warning(message: string) {
  warningMessages.push(String(message));
}

export function error(message: string) {
  errorMessages.push(String(message));
}
