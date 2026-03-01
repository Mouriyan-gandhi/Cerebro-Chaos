import { useState, useEffect, useCallback } from 'react';

export function useApi(apiFn, deps = [], autoLoad = true) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(autoLoad);
    const [error, setError] = useState(null);

    const execute = useCallback(async (...args) => {
        setLoading(true);
        setError(null);
        try {
            const result = await apiFn(...args);
            setData(result);
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, deps);

    useEffect(() => {
        if (autoLoad) {
            execute().catch(() => { });
        }
    }, [autoLoad]);

    return { data, loading, error, execute, setData };
}

export function usePolling(apiFn, interval = 3000, condition = true) {
    const { data, loading, error, execute, setData } = useApi(apiFn, [], false);

    useEffect(() => {
        if (!condition) return;

        execute().catch(() => { });
        const timer = setInterval(() => {
            execute().catch(() => { });
        }, interval);

        return () => clearInterval(timer);
    }, [condition, interval]);

    return { data, loading, error, execute, setData };
}
