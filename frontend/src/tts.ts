/**
 * Text-to-speech using the browser's built-in Web Speech API.
 *
 * No backend, no dependency, no network. Uses whatever voices the host
 * operating system provides. On Windows, this typically includes one or
 * more English voices. Hausa is not included by default -- when the
 * browser cannot find a matching voice, it falls back to the default
 * voice, which will read Hausa text with an English pronunciation.
 * That is a documented limitation, not a bug.
 */

export interface SpeakOptions {
  /** BCP-47 language tag, e.g. "en-NG", "en-US", "ha". */
  lang?: string;
  /** 0.1 - 10. Default 1. */
  rate?: number;
  /** 0 - 2. Default 1. */
  pitch?: number;
}

export class TextToSpeech {
  private utterance: SpeechSynthesisUtterance | null = null;
  private onEndCallback: (() => void) | null = null;

  /** True if the browser exposes the Web Speech API. */
  static isSupported(): boolean {
    return typeof window !== "undefined" && "speechSynthesis" in window;
  }

  /** Speak the given text. Cancels any in-flight speech first. */
  speak(text: string, options: SpeakOptions = {}): void {
    if (!TextToSpeech.isSupported()) {
      throw new Error("Text-to-speech is not supported in this browser.");
    }
    if (!text.trim()) {
      throw new Error("Nothing to speak.");
    }

    this.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = options.lang ?? "en-NG";
    utterance.rate = options.rate ?? 1;
    utterance.pitch = options.pitch ?? 1;

    // Prefer a voice that matches the requested language, if one exists.
    // Otherwise SpeechSynthesisUtterance uses the default voice.
    const matchingVoice = window.speechSynthesis
      .getVoices()
      .find((v) => v.lang.toLowerCase().startsWith(utterance.lang.toLowerCase().slice(0, 2)));
    if (matchingVoice) {
      utterance.voice = matchingVoice;
    }

    utterance.onend = () => {
      this.utterance = null;
      this.onEndCallback?.();
      this.onEndCallback = null;
    };
    utterance.onerror = () => {
      this.utterance = null;
      this.onEndCallback?.();
      this.onEndCallback = null;
    };

    this.utterance = utterance;
    window.speechSynthesis.speak(utterance);
  }

  /** Stop any in-flight speech immediately. */
  cancel(): void {
    if (TextToSpeech.isSupported()) {
      window.speechSynthesis.cancel();
    }
    this.utterance = null;
  }

  /** Register a callback to fire when the current speech finishes. */
  onEnd(callback: () => void): void {
    this.onEndCallback = callback;
  }

  isSpeaking(): boolean {
    return this.utterance !== null;
  }
}
