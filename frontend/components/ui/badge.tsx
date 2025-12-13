import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
    "inline-flex items-center rounded-sm px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border border-transparent backdrop-blur-sm",
    {
        variants: {
            variant: {
                default:
                    "bg-primary/10 text-primary border-primary/20 hover:bg-primary/20",
                secondary:
                    "bg-secondary/50 text-secondary-foreground hover:bg-secondary/60",
                destructive:
                    "bg-destructive/10 text-destructive border-destructive/20 hover:bg-destructive/20",
                success:
                    "bg-green-500/10 text-green-500 border-green-500/20 hover:bg-green-500/20",
                warning:
                    "bg-yellow-500/10 text-yellow-500 border-yellow-500/20 hover:bg-yellow-500/20",
                outline: "text-foreground border-border hover:bg-accent hover:text-accent-foreground",
                neon: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30 shadow-[0_0_10px_rgba(34,211,238,0.2)]",
            },
        },
        defaultVariants: {
            variant: "default",
        },
    }
)

export interface BadgeProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> { }

function Badge({ className, variant, ...props }: BadgeProps) {
    return (
        <div className={cn(badgeVariants({ variant }), className)} {...props} />
    )
}

export { Badge, badgeVariants }
