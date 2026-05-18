import { useRef, useState } from 'react'
import Card from './Card.jsx'

export default function Column({
  column,
  cards,
  canMoveLeft,
  canMoveRight,
  onDropCard,
  onMoveLeft,
  onMoveRight,
}) {
  const [isDragOver, setIsDragOver] = useState(false)
  const dragDepth = useRef(0)

  function handleDragOver(event) {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }

  function handleDrop(event) {
    event.preventDefault()
    setIsDragOver(false)
    dragDepth.current = 0

    const cardId = event.dataTransfer.getData('text/plain')
    if (!cardId) return
    onDropCard(cardId)
  }

  return (
    <section
      className={`column${isDragOver ? ' isDragOver' : ''}`}
      onDragEnter={() => {
        dragDepth.current += 1
        setIsDragOver(true)
      }}
      onDragLeave={() => {
        dragDepth.current -= 1
        if (dragDepth.current <= 0) {
          dragDepth.current = 0
          setIsDragOver(false)
        }
      }}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <div className="columnHeader">
        <div className="columnTitleRow">
          <h2 className="columnTitle">{column.title}</h2>
          <span className="badge" aria-label={`${cards.length} cards`}>
            {cards.length}
          </span>
        </div>
        <p className="columnHint">Drop cards here</p>
      </div>

      <div className="columnBody">
        {cards.length === 0 ? (
          <div className="empty">No emails</div>
        ) : (
          cards.map((card) => (
            <Card
              key={card.id}
              card={card}
              canMoveLeft={canMoveLeft}
              canMoveRight={canMoveRight}
              onMoveLeft={() => onMoveLeft(card.id)}
              onMoveRight={() => onMoveRight(card.id)}
            />
          ))
        )}
      </div>
    </section>
  )
}
