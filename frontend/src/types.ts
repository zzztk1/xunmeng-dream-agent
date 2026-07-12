export interface Fragment {
  id?: string
  type: string // text | voice | image | tag
  content: string
  order_index?: number
}

export interface Scene {
  text: string
  visual_prompt?: string
  recurring_entities?: string[]
  ambient?: string
  image_url?: string
  asset_id?: string
}

export interface Palette {
  bg: string
  colors: string[]
  accent: string
  ambient: string
}

export interface EmotionTag {
  label: string
  intensity: number
  source: string // ai | user
}

export interface Narrative {
  title: string
  global_style: string
  closing_reflection: string
  model: string
  scenes: Scene[]
}

export interface Dream {
  id: string
  title: string
  dream_date: string
  status: string // draft | generating | generated | failed
  primary_emotion: string | null
  palette: Palette | null
  cover_image_url: string | null
  created_at: string
  updated_at: string
  fragments: Fragment[]
  narrative: Narrative | null
  emotions: EmotionTag[]
}

export interface CalendarDay {
  count: number
  cover_image_url: string | null
  primary_emotion: string | null
  dream_ids: string[]
}

export interface CalendarData {
  month: string
  days: Record<string, CalendarDay>
}

export interface Health {
  ai_enabled: boolean
  llm_model: string
  image_model: string
}

export interface User {
  id: string
  username: string
  display_name: string
  is_guest?: boolean
}

export interface Insights {
  total: number
  emotions: { label: string; count: number }[]
  imagery: { word: string; count: number }[]
  by_month: { month: string; count: number }[]
}
