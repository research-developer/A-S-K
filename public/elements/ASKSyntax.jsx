import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

// Colors
const color = {
  op: "bg-blue-500 text-white",
  val: "bg-yellow-400 text-black",
  struct: "bg-orange-500 text-white",
  func: "bg-green-500 text-white",
  mod: "bg-fuchsia-500 text-white",
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

// One sequential syntax step - vertical frame
const SyntaxStepFrame = ({ index, element }) => {
  const semantic = element.semantic || "?"
  const surface = element.surface || ""
  
  // Determine type and color
  let stepType = 'val'
  if (typeof semantic === 'string' && semantic.includes('+')) stepType = 'struct'
  else if (surface && surface.length > 1 && !'aeiou'.includes(surface[0])) stepType = 'func'
  else if (typeof semantic === 'string' && !['a','e','i','o','u'].includes(semantic)) stepType = 'op'
  
  const parts = typeof semantic === "string" ? semantic.split("+") : []
  const hasStruct = parts.length > 1
  
  return (
    <div className="relative pl-6 py-2 w-full">
      {/* Left rail */}
      <div className="absolute left-2 top-0 bottom-0 w-px bg-zinc-800" />
      {/* Step number badge */}
      <div className="absolute -left-1 top-2 text-[10px] px-1 rounded bg-zinc-700 text-white">{index + 1}</div>

      {/* Surface form block */}
      <div className="inline-flex items-center gap-2">
        <NotchBlock className={color[stepType] + " inline-block"}>
          {surface || semantic}
        </NotchBlock>
      </div>

      {/* Semantic under surface */}
      <div className="mt-2 ml-2">
        {hasStruct ? (
          <NotchBlock className={color.struct + " inline-flex items-center gap-1"}>
            <span className="opacity-90 mr-1">Struct</span>
            {parts.map((p, i) => (
              <Chip key={i} type="val">{p}</Chip>
            ))}
          </NotchBlock>
        ) : semantic ? (
          <Chip type={stepType}>{semantic}</Chip>
        ) : (
          <span className="text-xs opacity-60">—</span>
        )}
      </div>
    </div>
  )
}

export default function ASKSyntax() {
  // props: { word, language, syntax, elements, overall_confidence }
  const elements = props.elements || []
  const percent = Math.round(((props.overall_confidence ?? 0) * 1000)) / 10
  const barColor = percent >= 80 ? "bg-green-500" : percent >= 60 ? "bg-yellow-500" : "bg-red-500"

  return (
    <Card className="w-full max-w-3xl">
      <CardContent className="p-4">
        {/* Title + Confidence */}
        <div className="flex items-center justify-between mb-3">
          <div className="text-lg font-semibold">
            USK Syntax: {props.word}
            {props.language && <span className="text-sm opacity-70 ml-2">({props.language})</span>}
          </div>
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

        {/* Sequential syntax: vertical step stack with rails */}
        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-2">
          {elements.length ? (
            elements.map((element, i) => (
              <SyntaxStepFrame 
                key={i} 
                index={i} 
                element={element}
              />
            ))
          ) : (
            <div className="p-3 opacity-60 text-sm">(no syntax elements)</div>
          )}
        </div>

        {/* Raw syntax (copy-friendly) */}
        {props.syntax && (
          <div className="mt-4 text-sm">
            <span className="opacity-80 mr-2">Raw:</span>
            <code className="px-2 py-1 rounded bg-zinc-800">{props.syntax}</code>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
