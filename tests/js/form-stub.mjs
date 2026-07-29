export const form = {
    plans: [],
    fields: [],
    ready: true,
    uploads: [],
    body: {},
    errorsShown: 0,
};


export function reset() {
    form.plans = [];
    form.fields = [];
    form.ready = true;
    form.uploads = [];
    form.body = {};
    form.errorsShown = 0;
}


export function compileForm(plan) {
    form.plans.push(plan);

    return {
        get fields() {
            return form.fields;
        },
        isReady: () => form.ready,
        showErrors: () => {
            form.errorsShown += 1;
        },
        uploads: () => form.uploads,
        read: () => form.body,
    };
}
