import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

// Run record type that matches the DB schema
export interface RunRecord {
  id: string;
  scenario: string;
  model: "ppo" | "hybrid";
  seed: number;
  return_value: number;
  completion_rate: number;
  containment_steps: number;
  duration: number;
  timestamp: string;
  pinned: boolean;
  tags: string[];
  config?: Record<string, unknown>;
}

// Helpers for run history persistence
export async function saveRun(run: Omit<RunRecord, 'timestamp' | 'id'>): Promise<RunRecord | null> {
  if (!supabase) {
    return null;
  }

  const runWithId = {
    ...run,
    id: `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString()
  };
  
  const { data, error } = await supabase
    .from('runs')
    .insert([runWithId])
    .select()
    .single();

  if (error) {
    console.error('Error saving run:', error);
    return null;
  }
  return data;
}

export async function getRuns(): Promise<RunRecord[]> {
  if (!supabase) {
    return [];
  }

  const { data, error } = await supabase
    .from('runs')
    .select('*')
    .order('timestamp', { ascending: false });

  if (error) {
    console.error('Error fetching runs:', error);
    return [];
  }
  return data || [];
}

export async function updateRunPin(id: string, pinned: boolean): Promise<boolean> {
  if (!supabase) {
    return false;
  }

  const { error } = await supabase
    .from('runs')
    .update({ pinned })
    .eq('id', id);

  if (error) {
    console.error('Error updating run:', error);
    return false;
  }
  return true;
}

export async function deleteRun(id: string): Promise<boolean> {
  if (!supabase) {
    return false;
  }

  const { error } = await supabase
    .from('runs')
    .delete()
    .eq('id', id);

  if (error) {
    console.error('Error deleting run:', error);
    return false;
  }
  return true;
}
