/**
 * @typedef {Object} PoolTask
 * @property {() => Promise<unknown>} asyncFn
 * @property {(value: unknown) => void} resolve
 * @property {(reason?: unknown) => void} reject
 */

/**
 * @typedef {Object} RunnerPool
 * @property {string} name
 * @property {number} maxConcurrency
 * @property {number} minIntervalMs
 * @property {PoolTask[]} queue
 * @property {number} running
 * @property {number} completed
 * @property {number} failed
 * @property {number} lastStartedAt
 * @property {NodeJS.Timeout | null} timer
 * @property {boolean} processing
 */

/**
 * Concurrent task runner with per-pool concurrency and rate limiting controls.
 */
export class ParallelRunner {
  constructor() {
    this._isShutdown = false;

    this.apiPool = this._createPool("apiPool", 4, 0);
    this.geminiPool = this._createPool("geminiPool", 3, 4000);
    this.copilotPool = this._createPool("copilotPool", 1, 2000);

    this._pools = {
      apiPool: this.apiPool,
      geminiPool: this.geminiPool,
      copilotPool: this.copilotPool,
    };
  }

  /**
   * Queue a single async function in the specified pool.
   *
   * @param {"apiPool" | "geminiPool" | "copilotPool"} poolName
   * @param {() => Promise<unknown>} asyncFn
   * @returns {Promise<unknown>}
   */
  runInPool(poolName, asyncFn) {
    if (typeof asyncFn !== "function") {
      throw new TypeError("asyncFn must be a function.");
    }

    if (this._isShutdown) {
      return Promise.reject(new Error("ParallelRunner has been shut down."));
    }

    const pool = this._getPool(poolName);

    return new Promise((resolve, reject) => {
      pool.queue.push({ asyncFn, resolve, reject });
      this._processPool(pool);
    });
  }

  /**
   * Run multiple async functions in the specified pool and resolve all results.
   *
   * @param {"apiPool" | "geminiPool" | "copilotPool"} poolName
   * @param {Array<() => Promise<unknown>>} arrayOfAsyncFns
   * @returns {Promise<unknown[]>}
   */
  runAll(poolName, arrayOfAsyncFns) {
    if (!Array.isArray(arrayOfAsyncFns)) {
      throw new TypeError("arrayOfAsyncFns must be an array of functions.");
    }

    const queuedPromises = arrayOfAsyncFns.map((fn) => this.runInPool(poolName, fn));
    return Promise.all(queuedPromises);
  }

  /**
   * Get current queue and execution stats for each pool.
   *
   * @returns {{
   *   apiPool: { queued: number, running: number, completed: number, failed: number },
   *   geminiPool: { queued: number, running: number, completed: number, failed: number },
   *   copilotPool: { queued: number, running: number, completed: number, failed: number }
   * }}
   */
  getStatus() {
    return {
      apiPool: this._getPoolStatus(this.apiPool),
      geminiPool: this._getPoolStatus(this.geminiPool),
      copilotPool: this._getPoolStatus(this.copilotPool),
    };
  }

  /**
   * Stop accepting new tasks and clear all queued tasks.
   * Running tasks are not force-stopped.
   */
  shutdown() {
    if (this._isShutdown) {
      return;
    }

    this._isShutdown = true;
    const shutdownError = new Error("ParallelRunner has been shut down.");

    for (const pool of Object.values(this._pools)) {
      if (pool.timer) {
        clearTimeout(pool.timer);
        pool.timer = null;
      }

      while (pool.queue.length > 0) {
        const task = pool.queue.shift();
        task.reject(shutdownError);
      }
    }
  }

  /**
   * @param {RunnerPool} pool
   * @returns {{ queued: number, running: number, completed: number, failed: number }}
   */
  _getPoolStatus(pool) {
    return {
      queued: pool.queue.length,
      running: pool.running,
      completed: pool.completed,
      failed: pool.failed,
    };
  }

  /**
   * @param {string} name
   * @param {number} maxConcurrency
   * @param {number} minIntervalMs
   * @returns {RunnerPool}
   */
  _createPool(name, maxConcurrency, minIntervalMs) {
    return {
      name,
      maxConcurrency,
      minIntervalMs,
      queue: [],
      running: 0,
      completed: 0,
      failed: 0,
      lastStartedAt: 0,
      timer: null,
      processing: false,
    };
  }

  /**
   * @param {string} poolName
   * @returns {RunnerPool}
   */
  _getPool(poolName) {
    const pool = this._pools[poolName];
    if (!pool) {
      throw new Error(
        `Unknown pool "${poolName}". Use "apiPool", "geminiPool", or "copilotPool".`
      );
    }
    return pool;
  }

  /**
   * @param {RunnerPool} pool
   */
  _processPool(pool) {
    if (this._isShutdown || pool.processing) {
      return;
    }

    pool.processing = true;
    try {
      while (
        !this._isShutdown &&
        pool.running < pool.maxConcurrency &&
        pool.queue.length > 0
      ) {
        const delayMs = this._getDelayMs(pool);
        if (delayMs > 0) {
          this._schedulePool(pool, delayMs);
          break;
        }

        const task = pool.queue.shift();
        this._startTask(pool, task);
      }
    } finally {
      pool.processing = false;
    }
  }

  /**
   * @param {RunnerPool} pool
   * @returns {number}
   */
  _getDelayMs(pool) {
    if (pool.minIntervalMs <= 0) {
      return 0;
    }

    const elapsedMs = Date.now() - pool.lastStartedAt;
    return Math.max(0, pool.minIntervalMs - elapsedMs);
  }

  /**
   * @param {RunnerPool} pool
   * @param {number} delayMs
   */
  _schedulePool(pool, delayMs) {
    if (pool.timer) {
      return;
    }

    pool.timer = setTimeout(() => {
      pool.timer = null;
      this._processPool(pool);
    }, delayMs);

    if (typeof pool.timer.unref === "function") {
      pool.timer.unref();
    }
  }

  /**
   * @param {RunnerPool} pool
   * @param {PoolTask} task
   */
  _startTask(pool, task) {
    pool.running += 1;
    pool.lastStartedAt = Date.now();

    Promise.resolve()
      .then(() => task.asyncFn())
      .then((result) => {
        pool.completed += 1;
        task.resolve(result);
      })
      .catch((error) => {
        pool.failed += 1;
        task.reject(error);
      })
      .finally(() => {
        pool.running -= 1;
        this._processPool(pool);
      });
  }
}
