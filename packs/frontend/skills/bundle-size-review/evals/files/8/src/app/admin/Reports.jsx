import moment from 'moment';

export default function Reports({ rows = [] }) {
  return (
    <table>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id}>
            <td>{r.ship}</td>
            <td>{moment(r.sailedAt).format('LL')}</td>
            <td>{moment(r.sailedAt).fromNow()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
