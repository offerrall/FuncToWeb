import { registerHooks } from "node:module";

const STUB = new URL("./form-stub.mjs", import.meta.url).href;
const PAGE = new URL("../../src/func_to_web/static/page.js", import.meta.url).href;

registerHooks({
    resolve(specifier, context, next) {
        const parent = context.parentURL ?? "";

        if (specifier === "./form.js" && parent.startsWith(PAGE)) {
            return { url: STUB, shortCircuit: true };
        }

        return next(specifier, context);
    },
});
