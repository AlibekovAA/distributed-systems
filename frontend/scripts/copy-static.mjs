import { cp, mkdir, readdir } from 'node:fs/promises';
import { dirname, extname, join, relative } from 'node:path';

const sourceRoot = 'src';
const outputRoot = 'dist';

async function copyStaticFiles(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
        const source = join(directory, entry.name);
        if (entry.isDirectory()) {
            await copyStaticFiles(source);
        } else if (extname(entry.name) !== '.ts') {
            const destination = join(outputRoot, relative(sourceRoot, source));
            await mkdir(dirname(destination), { recursive: true });
            await cp(source, destination);
        }
    }
}

await mkdir(outputRoot, { recursive: true });
await copyStaticFiles(sourceRoot);
