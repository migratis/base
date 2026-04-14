import Pagination from 'react-bootstrap/Pagination';

const MigratisPagination = (props) => {

  return (
    <>
      { props.pages > 1 &&
        <Pagination className="justify-content-center mt-3">
          <Pagination.First onClick={() => props.setPage(1)} disabled={props.page === 1}/>
          <Pagination.Prev onClick={() => props.setPage(Math.max(props.page - 1, 1))} disabled={props.page === 1}/>
      
          {[...Array(props.pages)].map((_, i) => (
            <Pagination.Item
              key={i+1}
              active={i+1 === props.page}
              onClick={() => props.setPage(i+1)}
            >
              {i+1}
            </Pagination.Item>
          ))}
      
          <Pagination.Next onClick={() => props.setPage(Math.min(props.page + 1, props.pages))} disabled={props.page === props.pages}/>
          <Pagination.Last onClick={() => props.setPage(props.pages)} disabled={props.page === props.pages}/>
        </Pagination>
      }
    </>
  );
};

export default MigratisPagination;


