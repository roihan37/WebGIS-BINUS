<script>
  export let state;
  export let title;
  export let retry;
  export let cancel;
</script>
{#if state?.status && state.status !== 'idle'}
  <div class="feedback" class:error={state.status === 'error'} role={state.status === 'error' ? 'alert' : 'status'} aria-live="polite">
    {#if state.status === 'loading'}<span class="spinner" aria-hidden="true"></span><strong>{title}</strong><p>Mohon tunggu, peta tetap dapat digeser.</p><button on:click={cancel}>Batalkan</button>
    {:else}<p>{state.message}</p>{#if state.status === 'error'}<button on:click={retry}>Coba lagi</button>{/if}{/if}
  </div>
{/if}
<style>
  .feedback { margin: 12px 0; padding: 12px; background: #edf4ef; border: 1px solid #d3e5d8; border-radius: 10px; font-size: 12px; color: #315941; }
  .feedback.error { background: #fff4ee; border-color: #f3cfbc; color: #943d24; }
  p { margin: 6px 0; line-height: 1.5; } strong { font-size: 12px; }
  button { border: 1px solid currentColor; color: inherit; background: transparent; padding: 6px 10px; border-radius: 6px; cursor: pointer; margin-top: 5px; }
  .spinner { display: inline-block; width: 13px; height: 13px; border: 2px solid #bbcebf; border-top-color: #166348; border-radius: 50%; margin-right: 8px; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media(prefers-reduced-motion: reduce) { .spinner { animation: none; } }
</style>
