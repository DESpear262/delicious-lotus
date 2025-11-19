

/**
 * Home Page Component
 *
 * Landing page placeholder for the AI Video Generation Pipeline.
 * Full implementation will be added in PR-F006 (Pipeline Selection).
 */
export function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-8 bg-background">
      <div className="text-center max-w-2xl">
        <h1 className="text-4xl font-bold text-foreground mb-4">Delicious Lotus</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Welcome to Delicious Lotus
        </p>
        <p className="text-sm text-muted-foreground bg-muted px-4 py-2 rounded-md inline-block">
          Pipeline selection coming in PR-F006
        </p>
      </div>
    </div>
  );
}
