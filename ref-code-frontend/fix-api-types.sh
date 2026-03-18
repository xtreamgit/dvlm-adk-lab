#!/bin/bash
# Fix TypeScript any types and unused variables in api-enhanced.ts

FILE="src/lib/api-enhanced.ts"

# Replace all 'any' with 'unknown' for generic types
sed -i '' 's/Promise<any>/Promise<unknown>/g' "$FILE"
sed -i '' 's/: any\[\]/: unknown[]/g' "$FILE"
sed -i '' 's/: any)/: unknown)/g' "$FILE"
sed -i '' 's/: any;/: unknown;/g' "$FILE"
sed -i '' 's/(err: any)/(err: unknown)/g' "$FILE"
sed -i '' 's/(e: any)/(e: unknown)/g' "$FILE"

# Fix unused catch variables by prefixing with underscore
sed -i '' 's/} catch (e) {/} catch (_e) {/g' "$FILE"

echo "Fixed TypeScript types in $FILE"
