function MyButton() {
    return (
        <button>I am a button</button>
    )
}

const products = [
  { title: 'Cabbage', id: 1 },
  { title: 'Garlic', id: 2 },
  { title: 'Apple', id: 3 },
];


export default function MyTable(){  
  
    
  const ListItems = products.map(product =>
    <li key={product.id}>
      {product.title}
    </li>
  )
  return (
    <div>
        <h1>Welcome to My Table</h1>
        <MyButton />
      <ul>{ListItems}</ul>
    </div>
  )
}

