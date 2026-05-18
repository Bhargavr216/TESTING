export default function Card({
  card,
  canMoveLeft,
  canMoveRight,
  onMoveLeft,
  onMoveRight,
}) {
  function handleDragStart(event) {
    event.dataTransfer.setData('text/plain', card.id)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <article className="card" draggable onDragStart={handleDragStart}>
      <div className="cardHeader">
        <h3 className="cardTitle" title={card.title}>
          {card.title}
        </h3>
        <div className="cardActions">
          <button
            className="iconButton"
            type="button"
            onClick={onMoveLeft}
            disabled={!canMoveLeft}
            aria-label="Move left"
            title="Move left"
          >
            ←
          </button>
          <button
            className="iconButton"
            type="button"
            onClick={onMoveRight}
            disabled={!canMoveRight}
            aria-label="Move right"
            title="Move right"
          >
            →
          </button>
        </div>
      </div>

      {card.description ? <p className="cardDescription">{card.description}</p> : null}

      {card.url ? (
        <a className="linkButton" href={card.url} target="_blank" rel="noreferrer">
          Open in Gmail
        </a>
      ) : null}
    </article>
  )
}
