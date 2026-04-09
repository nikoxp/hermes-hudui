import { useApi } from '../hooks/useApi'
import Panel, { Sparkline } from './Panel'
import { formatTokens } from '../lib/utils'

function CostCard({ label, tokens, cost, color }: { label: string; tokens: number; cost: number; color: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 px-2" style={{ borderLeft: `2px solid ${color}` }}>
      <div>
        <div className="text-[12px]">{label}</div>
        <div className="text-[11px]" style={{ color: 'var(--hud-text-dim)' }}>{formatTokens(tokens)} tokens</div>
      </div>
      <div className="text-[14px] font-bold tabular-nums" style={{ color }}>
        ${cost.toFixed(2)}
      </div>
    </div>
  )
}

function TokenBreakdown({ data, breakdown, pricing }: { data: any; breakdown: any; pricing: any }) {
  const rows = [
    { label: 'Input (standard)', tokens: data.input_tokens, cost: breakdown.input, color: 'var(--hud-primary)' },
    { label: 'Output', tokens: data.output_tokens, cost: breakdown.output, color: 'var(--hud-accent)' },
    { label: 'Cache Read', tokens: data.cache_read_tokens, cost: breakdown.cache_read, color: 'var(--hud-success)' },
    { label: 'Cache Write', tokens: data.cache_write_tokens, cost: breakdown.cache_write, color: 'var(--hud-warning)' },
    { label: 'Reasoning', tokens: data.reasoning_tokens, cost: breakdown.reasoning, color: 'var(--hud-secondary)' },
  ]

  return (
    <div className="space-y-1.5">
      {/* Pricing reference */}
      <div className="text-[10px] mb-3 p-2" style={{ background: 'var(--hud-bg-panel)', color: 'var(--hud-text-dim)' }}>
        Pricing (per 1M tokens): in ${pricing.input} · out ${pricing.output} · cache_r ${pricing.cache_read} · cache_w ${pricing.cache_write} · reasoning ${pricing.reasoning}
      </div>

      {rows.map(r => (
        <CostCard key={r.label} label={r.label} tokens={r.tokens} cost={r.cost} color={r.color} />
      ))}

      {/* Total bar */}
      <div className="mt-2 pt-2" style={{ borderTop: '1px solid var(--hud-border)' }}>
        <div className="flex justify-between items-center">
          <span className="text-[12px] font-bold">TOTAL</span>
          <span className="text-[12px]" style={{ color: 'var(--hud-text-dim)' }}>{formatTokens(data.total_tokens)} tokens</span>
        </div>
      </div>
    </div>
  )
}

export default function TokenCostsPanel() {
  const { data, isLoading } = useApi('/token-costs', 60000)

  if (isLoading || !data) {
    return <Panel title="Token Costs" className="col-span-full"><div className="glow text-[12px] animate-pulse">Calculating costs...</div></Panel>
  }

  const { today, all_time: allTime, cost_breakdown: breakdown, daily_trend: dailyTrend, pricing, model } = data
  const costValues = dailyTrend.map((d: any) => d.cost)
  const tokenValues = dailyTrend.map((d: any) => d.tokens)

  return (
    <>
      {/* Today vs All-time summary */}
      <Panel title={`Today — $${today.estimated_cost_usd.toFixed(2)}`}>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="text-center p-2" style={{ background: 'var(--hud-bg-panel)' }}>
            <div className="stat-value text-[18px]">{today.session_count}</div>
            <div className="stat-label">sessions today</div>
          </div>
          <div className="text-center p-2" style={{ background: 'var(--hud-bg-panel)' }}>
            <div className="stat-value text-[18px]">{today.message_count}</div>
            <div className="stat-label">messages today</div>
          </div>
        </div>
        <div className="text-[12px] space-y-1">
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>Input tokens</span>
            <span>{formatTokens(today.input_tokens)}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>Output tokens</span>
            <span>{formatTokens(today.output_tokens)}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>Cache read</span>
            <span>{formatTokens(today.cache_read_tokens)}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>Cache write</span>
            <span>{formatTokens(today.cache_write_tokens)}</span>
          </div>
          <div className="flex justify-between font-bold pt-1" style={{ borderTop: '1px solid var(--hud-border)' }}>
            <span>Total tokens</span>
            <span>{formatTokens(today.total_tokens)}</span>
          </div>
        </div>
        <div className="mt-3 text-[20px] font-bold text-center" style={{ color: 'var(--hud-accent)' }}>
          ${today.estimated_cost_usd.toFixed(2)}
        </div>
        <div className="text-[10px] text-center" style={{ color: 'var(--hud-text-dim)' }}>estimated today</div>
      </Panel>

      {/* All-time summary */}
      <Panel title={`All Time — $${allTime.estimated_cost_usd.toFixed(2)}`}>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="text-center p-2" style={{ background: 'var(--hud-bg-panel)' }}>
            <div className="stat-value text-[18px]">{allTime.session_count}</div>
            <div className="stat-label">sessions</div>
          </div>
          <div className="text-center p-2" style={{ background: 'var(--hud-bg-panel)' }}>
            <div className="stat-value text-[18px]">{(allTime.message_count || 0).toLocaleString()}</div>
            <div className="stat-label">messages</div>
          </div>
          <div className="text-center p-2" style={{ background: 'var(--hud-bg-panel)' }}>
            <div className="stat-value text-[18px]">{formatTokens(allTime.total_tokens)}</div>
            <div className="stat-label">total tokens</div>
          </div>
          <div className="text-center p-2" style={{ background: 'var(--hud-bg-panel)' }}>
            <div className="stat-value text-[18px]">{(allTime.tool_call_count || 0).toLocaleString()}</div>
            <div className="stat-label">tool calls</div>
          </div>
        </div>
        <div className="mt-2 text-[20px] font-bold text-center" style={{ color: 'var(--hud-accent)' }}>
          ${allTime.estimated_cost_usd.toFixed(2)}
        </div>
        <div className="text-[10px] text-center" style={{ color: 'var(--hud-text-dim)' }}>
          estimated all-time ({model})
        </div>
      </Panel>

      {/* Cost breakdown */}
      <Panel title="Cost Breakdown">
        <TokenBreakdown data={allTime} breakdown={breakdown} pricing={pricing} />
        <div className="mt-3 text-[16px] font-bold flex justify-between">
          <span>Total estimated cost</span>
          <span style={{ color: 'var(--hud-accent)' }}>${allTime.estimated_cost_usd.toFixed(2)}</span>
        </div>
      </Panel>

      {/* Daily cost trend */}
      <Panel title="Daily Cost Trend" className="col-span-full">
        <div className="grid grid-cols-2 gap-4 mb-3">
          <div>
            <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--hud-text-dim)' }}>
              Cost/day (USD)
            </div>
            <Sparkline values={costValues} width={500} height={50} />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--hud-text-dim)' }}>
              Tokens/day
            </div>
            <Sparkline values={tokenValues} width={500} height={50} />
          </div>
        </div>
        <div className="text-[12px] grid grid-cols-5 gap-1">
          {dailyTrend.slice(-10).map((d: any) => (
            <div key={d.date} className="text-center py-1" style={{ background: 'var(--hud-bg-panel)' }}>
              <div style={{ color: 'var(--hud-text-dim)' }}>{d.date.slice(5)}</div>
              <div style={{ color: 'var(--hud-accent)' }}>${d.cost.toFixed(2)}</div>
              <div>{formatTokens(d.tokens)}</div>
            </div>
          ))}
        </div>
      </Panel>
    </>
  )
}
