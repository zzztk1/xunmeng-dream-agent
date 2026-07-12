/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Web Speech API（语音录入），不同浏览器前缀不同
interface Window {
  SpeechRecognition?: any
  webkitSpeechRecognition?: any
  webkitAudioContext?: typeof AudioContext
}
