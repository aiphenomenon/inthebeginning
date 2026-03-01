<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="10">
    <title>In The Beginning — Cosmic Simulation</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <h1>In The Beginning</h1>
    <h2>Cosmic Simulation Snapshot &mdash; Seed #<?= htmlspecialchars((string)$state['seed']) ?></h2>

    <div class="progress-bar">
        <div class="progress-fill" style="width: <?= round(($state['epoch_index'] / 12) * 100) ?>%"></div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Current State</h3>
            <div class="stat">
                <span class="stat-label">Epoch</span>
                <span class="stat-value"><?= htmlspecialchars($state['current_epoch']) ?></span>
            </div>
            <div class="stat">
                <span class="stat-label">Temperature</span>
                <span class="stat-value"><?= sprintf('%.2e K', $state['temperature']) ?></span>
            </div>
            <div class="stat">
                <span class="stat-label">Scale Factor</span>
                <span class="stat-value"><?= sprintf('%.2e', $state['scale_factor']) ?></span>
            </div>
            <div class="stat">
                <span class="stat-label">Elapsed</span>
                <span class="stat-value"><?= $state['elapsed_seconds'] ?>s</span>
            </div>
        </div>

        <div class="card">
            <h3>Statistics</h3>
            <div class="stat">
                <span class="stat-label">Particles Created</span>
                <span class="stat-value"><?= number_format($state['stats']['particles_created']) ?></span>
            </div>
            <div class="stat">
                <span class="stat-label">Atoms Formed</span>
                <span class="stat-value"><?= number_format($state['stats']['atoms_formed']) ?></span>
            </div>
            <div class="stat">
                <span class="stat-label">Molecules Formed</span>
                <span class="stat-value"><?= number_format($state['stats']['molecules_formed']) ?></span>
            </div>
            <div class="stat">
                <span class="stat-label">Lifeforms</span>
                <span class="stat-value"><?= number_format($state['stats']['lifeforms_created']) ?></span>
            </div>
        </div>
    </div>

    <div class="card">
        <h3>Epoch Timeline</h3>
        <ul class="epoch-list">
            <?php foreach ($state['epochs'] as $i => $epoch): ?>
            <li class="epoch-item">
                <span class="epoch-idx"><?= $i ?></span>
                <span class="epoch-name"><?= htmlspecialchars($epoch['epoch']) ?></span>
                <span class="epoch-temp"><?= sprintf('%.2e K', $epoch['temperature']) ?></span>
            </li>
            <?php endforeach; ?>
        </ul>
    </div>

    <footer>
        Auto-refreshes every 10 seconds &bull;
        <a href="/api/state" style="color: var(--accent)">JSON API</a> &bull;
        <a href="/api/reset" style="color: var(--accent)">Reset</a>
    </footer>
</body>
</html>
