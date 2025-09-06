import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

// Colors
const color = {
  op: "bg-blue-500 text-white",
  val: "bg-yellow-400 text-black",
  struct: "bg-orange-500 text-white",
}

// Notched block (Scratch-like)
const NotchBlock = ({ children, className = "" }) => (
  <div
    className={
      "relative rounded-md px-3 py-1 text-xs shadow-sm " +
      "before:content-[''] before:absolute before:-top-[6px] before:left-3 before:w-3 before:h-3 before:bg-background before:rounded-b-sm " +
      className
    }
  >
    {children}
  </div>
)

// Value chip
const Chip = ({ children, type = "val" }) => (
  <span className={"rounded-md px-2 py-0.5 text-xs " + color[type]}>{children}</span>
)

// Chevron
const Arrow = () => <span className="mx-2 opacity-60">›</span>

// One sequential step (operator over payloads) - vertical frame
const StepFrame = ({ index, op, payload, position, principle }) => {
  const parts = typeof payload === "string" ? payload.split("+") : []
  const hasStruct = parts.length > 1
  
  const positionColor = {
    initial: "bg-green-600",
    medial: "bg-blue-600", 
    final: "bg-orange-600"
  }[position] || "bg-zinc-600"
  
  return (
    <div className="relative pl-6 py-2 w-full">
      {/* Left rail */}
      <div className="absolute left-2 top-0 bottom-0 w-px bg-zinc-800" />
      {/* Step number badge */}
      <div className="absolute -left-1 top-2 text-[10px] px-1 rounded bg-zinc-700 text-white">{index + 1}</div>

      {/* Operator block with tooltip */}
      <div className="inline-flex items-center gap-2">
        <NotchBlock 
          className={color.op + " inline-block cursor-help"} 
          title={principle ? `${op} (${principle})` : op}
        >
          {op || "?"}
        </NotchBlock>
        {/* Position badge */}
        {position && (
          <span className={`text-[10px] px-1 py-0.5 rounded text-white ${positionColor}`}>
            {position[0].toUpperCase()}
          </span>
        )}
      </div>

      {/* Payloads under operator */}
      <div className="mt-2 ml-2">
        {hasStruct ? (
          <NotchBlock className={color.struct + " inline-flex items-center gap-1"}>
            <span className="opacity-90 mr-1">Struct</span>
            {parts.map((p, i) => (
              <Chip key={i} type="val">{p}</Chip>
            ))}
          </NotchBlock>
        ) : payload ? (
          <Chip type="val">{payload}</Chip>
        ) : (
          <span className="text-xs opacity-60">—</span>
        )}
      </div>
    </div>
  )
}

export default function ASKDecode() {
  // props: { word, operators, payloads, pairs, program, gloss, confidence }
  const program = props.program || null
  const ops = Array.isArray(props.operators) ? props.operators : []
  const payloads = Array.isArray(props.payloads) ? props.payloads : []
  const pairs = Array.isArray(props.pairs) ? props.pairs : []

  // Build steps sequentially: prefer structured program
  let steps = []
  if (program && Array.isArray(program.steps)) {
    steps = program.steps.map((s) => ({ 
      op: s.op, 
      payload: s.payload, 
      position: s.position, 
      principle: s.principle,
      index: s.index 
    }))
  } else if (pairs.length) {
    steps = pairs.map((it, i) => ({ 
      op: it[0], 
      payload: it[1], 
      index: i,
      position: i === 0 ? "initial" : (i === pairs.length - 1 ? "final" : "medial")
    }))
  } else if (ops.length) {
    steps = ops.map((op, i) => ({ 
      op, 
      payload: payloads[i], 
      index: i,
      position: i === 0 ? "initial" : (i === ops.length - 1 ? "final" : "medial")
    }))
  }

  // Header text from signature or gloss
  const signatureText = program?.signature?.text
  const functionLine = signatureText || props.gloss || (ops.length ? ops.join(" → ") : "")
  const percent = Math.round(((props.confidence ?? 0) * 1000)) / 10
  const barColor = percent >= 80 ? "bg-green-500" : percent >= 60 ? "bg-yellow-500" : "bg-red-500"

  return (
    <Card className="w-full max-w-3xl">
      <CardContent className="p-4">
        {/* Title + Confidence */}
        <div className="flex items-center justify-between mb-3">
          <div className="text-lg font-semibold">Decoding: {props.word}</div>
          <div className="flex items-center gap-2">
            <div className="w-28 h-2 bg-zinc-800 rounded">
              <div
                className={`h-2 ${barColor} rounded`}
                style={{ width: `${isNaN(percent) ? 0 : percent}%` }}
              />
            </div>
            <Badge variant="outline">{isNaN(percent) ? "—" : `${percent}%`}</Badge>
          </div>
        </div>

        {/* Sequential program: vertical step stack with rails */}
        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-2">
          {steps.length ? (
            steps.map((s, i) => (
              <StepFrame 
                key={i} 
                index={s.index !== undefined ? s.index : i} 
                op={s.op} 
                payload={s.payload}
                position={s.position}
                principle={s.principle}
              />
            ))
          ) : (
            <div className="p-3 opacity-60 text-sm">(no steps)</div>
          )}
        </div>

        {/* Raw function (copy-friendly) */}
        {functionLine && (
          <div className="mt-4 text-sm">
            <span className="opacity-80 mr-2">Raw:</span>
            <code className="px-2 py-1 rounded bg-zinc-800">{functionLine}</code>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
